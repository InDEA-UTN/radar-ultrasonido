/*
 * test_sensor.ino
 * 
 * Programa de prueba para el sensor ultrasónico HC-SR04.
 * Proyecto: Radar de Ultrasonido (InDEA - UTN FRM)
 * Fase 2: Comprobación de componentes por separado.
 * 
 * Conexiones HC-SR04 con Arduino Uno:
 *   - VCC  -> 5V
 *   - GND  -> GND
 *   - TRIG -> Pin D11
 *   - ECHO -> Pin D12
 * 
 * Salida serie adaptada al protocolo (docs/protocolo.md):
 *   <angulo>,<distancia_mm>,<estado>
 *   Baudrate: 115200 bps
 */

const uint8_t PIN_TRIG = 11;
const uint8_t PIN_ECHO = 12;

// Ángulo simulado/fijo para la prueba individual del sensor (90° = centro)
const int ANGULO_FIJO = 90;

// Constantes de distancia y tiempo (en mm)
const unsigned int DISTANCIA_MIN_MM = 40;    // 4 cm
const unsigned int DISTANCIA_MAX_MM = 4000;  // 4 metros
// Timeout para pulseIn: 4000 mm * 58 us/cm / 10 = ~23200 us (usamos 25 ms)
const unsigned long TIMEOUT_ECHO_US = 25000;

void setup() 
{
  Serial.begin(115200);
  while (!Serial && millis() < 2000);

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  digitalWrite(PIN_TRIG, LOW);

  // Cabecera de diagnóstico según protocolo
  Serial.println(F("# radar-ultrasonido test_sensor v0.1 baud=115200 rango_mm=40..4000"));
}

void loop() 
{
  // 1. Generar pulso de disparo de 10us en TRIG
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(4);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // 2. Medir duración del eco en microsegundos con timeout de seguridad
  unsigned long duracion_us = pulseIn(PIN_ECHO, HIGH, TIMEOUT_ECHO_US);

  int distancia_mm = 0;
  int estado = 0;

  // 3. Procesar medición y determinar estado
  if (duracion_us == 0) {
    // Sin eco recibido (tiempo agotado o fuera de rango)
    distancia_mm = 0;
    estado = 1;
  } else {
    // Cálculo de distancia en milímetros: (t_us * 343 mm/ms) / 2000
    // Equivalente simplificado a 20°C: (t_us * 10) / 58
    distancia_mm = (duracion_us * 10) / 58;

    if (distancia_mm < DISTANCIA_MIN_MM || distancia_mm > DISTANCIA_MAX_MM) {
      estado = 1; // Fuera del rango útil del sensor
    } else {
      estado = 0; // Medición válida
    }
  }

  // 4. Emitir trama según protocolo: <angulo>,<distancia_mm>,<estado>
  Serial.print(ANGULO_FIJO);
  Serial.print(',');
  Serial.print(distancia_mm);
  Serial.print(',');
  Serial.println(estado);

  // 5. Espera entre disparos recomendada (60 ms para evitar ecos residuales en el ambiente)
  delay(60);
}

