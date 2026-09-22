/*
 * radar.ino
 *
 * Firmware integrado para el Radar de Ultrasonido (InDEA - UTN FRM).
 * Fase 4: Adquisición integrada (Barrido del Servo + Medición Ultrasónica).
 *
 * Conexiones de Hardware:
 *   - Servo SG90:
 *       * Naranja (Señal) -> Pin D9 (PWM)
 *       * Rojo (VCC)       -> 5V
 *       * Marrón/Negro     -> GND
 *   - Sensor HC-SR04:
 *       * VCC              -> 5V
 *       * GND              -> GND
 *       * TRIG             -> Pin D11
 *       * ECHO             -> Pin D12
 *
 * Protocolo de comunicación (docs/protocolo.md):
 *   - Formato serie: <angulo>,<distancia_mm>,<estado>
 *   - Baudrate: 115200 bps (8N1)
 *   - Estados: 0 = Válido, 1 = Fuera de rango / Sin eco
 */

#include <Servo.h>

// ==========================================
// Configuración de Pines
// ==========================================
const uint8_t PIN_SERVO = 9;
const uint8_t PIN_TRIG = 11;
const uint8_t PIN_ECHO = 12;

// ==========================================
// Parámetros de Barrido del Servo
// ==========================================
const int ANGULO_MIN = 0;   // Límite inferior (ajustar si zumba en el tope)
const int ANGULO_MAX = 180; // Límite superior (ajustar si zumba en el tope)
const int PASO_ANGULO = 1;  // Incremento en grados por medición (1° o 2°)

// Tiempos de temporización (en milisegundos)
// Asentamiento mecánico del SG90 antes de medir
const unsigned long TIEMPO_ASENTAMIENTO_MS = 25;
// Tiempo de guarda adicional para disipar ecos residuales (~60ms totales por
// ciclo)
const unsigned long TIEMPO_ENTRE_DISPAROS_MS = 35;

// ==========================================
// Parámetros del Sensor HC-SR04
// ==========================================
const unsigned int DISTANCIA_MIN_MM = 40;    // 40 mm (4 cm)
const unsigned int DISTANCIA_MAX_MM = 4000;  // 4000 mm (4 metros)
const unsigned long TIMEOUT_ECHO_US = 25000; // ~25 ms timeout (~4.3 m)

// ==========================================
// Variables de Estado
// ==========================================
Servo servoRadar;
int anguloActual = 0;
int direccion = 1; // +1 hacia 180°, -1 hacia 0°
bool barridoActivo = true;

// ==========================================
// Funciones Auxiliares
// ==========================================

void enviarCabecera() {
  Serial.print(F("# radar-ultrasonido v1.0 paso="));
  Serial.print(PASO_ANGULO);
  Serial.print(F(" baud=115200 rango_mm="));
  Serial.print(DISTANCIA_MIN_MM);
  Serial.print(F(".."));
  Serial.println(DISTANCIA_MAX_MM);
}

/**
 * Realiza un disparo con el HC-SR04 y calcula la distancia en milímetros.
 * Retorna:
 *   distancia_mm: Distancia calculada en mm.
 *   estado: 0 si es válida, 1 si no hubo eco o está fuera de rango.
 */
void medirDistancia(int &distancia_mm, int &estado) {
  // 1. Disparo de pulso limpio de 10us en TRIG
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(4);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // 2. Medir duración del eco con pulseIn y timeout de seguridad
  unsigned long duracion_us = pulseIn(PIN_ECHO, HIGH, TIMEOUT_ECHO_US);

  if (duracion_us == 0) {
    // Sin eco (tiempo agotado)
    distancia_mm = 0;
    estado = 1;
  } else {
    // Cálculo a 20°C: distancia_mm = (duracion_us * 10) / 58
    distancia_mm = (duracion_us * 10) / 58;

    if (distancia_mm < DISTANCIA_MIN_MM || distancia_mm > DISTANCIA_MAX_MM) {
      estado = 1; // Fuera del rango detectable útil
    } else {
      estado = 0; // Medición válida
    }
  }
}

/**
 * Procesa comandos de control opcionales enviados desde la PC
 */
void procesarComandosSerie() {
  while (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'P' || cmd == 'p') {
      barridoActivo = false;
      Serial.println(F("# Barrido pausado"));
    } else if (cmd == 'S' || cmd == 's') {
      barridoActivo = true;
      Serial.println(F("# Barrido iniciado"));
    } else if (cmd == 'Z' || cmd == 'z') {
      anguloActual = ANGULO_MIN;
      servoRadar.write(anguloActual);
      Serial.println(F("# Posicion reajustada a 0 grados"));
    } else if (cmd == 'C' || cmd == 'c') {
      anguloActual = 90;
      servoRadar.write(anguloActual);
      Serial.println(F("# Posicion centrada a 90 grados"));
    } else if (cmd == '?') {
      enviarCabecera();
    }
  }
}

// ==========================================
// Setup
// ==========================================
void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 2000)
    ; // Espera en placas nativas USB

  // Configuración de pines del HC-SR04
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  digitalWrite(PIN_TRIG, LOW);

  // Inicialización del servo
  servoRadar.attach(PIN_SERVO);
  anguloActual = ANGULO_MIN;
  servoRadar.write(anguloActual);

  // Esperar a que el servo llegue a la posición inicial
  delay(500);

  // Cabecera inicial de diagnóstico para la interfaz
  enviarCabecera();
}

// ==========================================
// Loop Principal
// ==========================================
void loop() {
  // 1. Revisar si llegaron comandos desde la GUI o el monitor serie
  procesarComandosSerie();

  if (!barridoActivo) {
    delay(50);
    return;
  }

  // 2. Mover el servo a la posición del ángulo actual
  servoRadar.write(anguloActual);

  // 3. Esperar el asentamiento mecánico del servo antes de medir
  delay(TIEMPO_ASENTAMIENTO_MS);

  // 4. Medir distancia ultrasónica
  int distancia_mm = 0;
  int estado = 0;
  medirDistancia(distancia_mm, estado);

  // 5. Emitir trama por el puerto serie siguiendo el protocolo:
  // <angulo>,<distancia_mm>,<estado>
  Serial.print(anguloActual);
  Serial.print(',');
  Serial.print(distancia_mm);
  Serial.print(',');
  Serial.println(estado);

  // 6. Tiempo de guarda para evitar ecos residuales en el ambiente (~60ms ciclo
  // total)
  delay(TIEMPO_ENTRE_DISPAROS_MS);

  // 7. Calcular el siguiente ángulo del barrido (ida y vuelta: 0° -> 180° ->
  // 0°)
  anguloActual += (direccion * PASO_ANGULO);

  if (anguloActual >= ANGULO_MAX) {
    anguloActual = ANGULO_MAX;
    direccion = -1; // Cambiar sentido hacia 0°
  } else if (anguloActual <= ANGULO_MIN) {
    anguloActual = ANGULO_MIN;
    direccion = 1; // Cambiar sentido hacia 180°
  }
}
