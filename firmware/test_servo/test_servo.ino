/*
 * test_servo.ino
 *
 * Programa de prueba y calibración para el micro servo SG90.
 * Proyecto: Radar de Ultrasonido (InDEA - UTN FRM)
 * Fase 2: Comprobación de componentes por separado.
 *
 * Conexiones SG90:
 *   - Naranja (Señal): Pin D9 (o cualquier pin PWM)
 *   - Rojo (VCC): 5V (fuente externa recomendada o 5V Arduino)
 *   - Marrón/Negro (GND): GND (¡común con Arduino!)
 *
 * Modos de uso desde el Monitor Serie (115200 baudios):
 *   - Ingresar un número entre 0 y 180 para mover a ese ángulo exacto.
 *   - 'c' -> Centrar a 90° (ideal para montar/alinear el brazo mecánico).
 *   - 's' -> Alternar barrido automático continuo (Sweep 0° <-> 180°).
 *   - 'p' -> Prueba por pasos (0°, 45°, 90°, 135°, 180°).
 *   - '+' / '-' -> Incrementar / decrementar ángulo en 5°.
 */

#include <Servo.h>

// --- Configuración de Pines y Parámetros ---
const uint8_t PIN_SERVO = 9;

// Límites de seguridad para evitar forzar los topes mecánicos del SG90
const int ANGULO_MIN = 0;   // Si zumba en 0, ajustar ej. a 5 o 10
const int ANGULO_MAX = 180; // Si zumba en 180, ajustar ej. a 170 o 175

Servo servoRadar;

int anguloActual = 90;
bool modoBarrido = false;
int incrementoBarrido = 1;
unsigned long ultimoPasoBarrido = 0;
const unsigned long INTERVALO_BARRIDO_MS = 20; // Velocidad del barrido continuo

void imprimirMenu() {
  Serial.println(F("\n=========================================="));
  Serial.println(F("   PRUEBA Y CALIBRACIÓN SERVO SG90 - InDEA"));
  Serial.println(F("=========================================="));
  Serial.println(F("Comandos disponibles en el Monitor Serie:"));
  Serial.println(F("  [0 - 180] : Mover al ángulo deseado"));
  Serial.println(F("  'c'       : Centrar a 90 grados"));
  Serial.println(F("  's'       : Iniciar / Detener barrido automático"));
  Serial.println(
      F("  'p'       : Prueba rápida por pasos (0, 45, 90, 135, 180)"));
  Serial.println(F("  '+' / '-' : Mover +/- 5 grados"));
  Serial.println(F("==========================================\n"));
}

void moverA(int nuevoAngulo) {
  nuevoAngulo = constrain(nuevoAngulo, ANGULO_MIN, ANGULO_MAX);
  anguloActual = nuevoAngulo;
  servoRadar.write(anguloActual);
  Serial.print(F("-> Posición actual: "));
  Serial.print(anguloActual);
  Serial.println(F("°"));
}

void pruebaPorPasos() {
  const int pasos[] = {0, 45, 90, 135, 180, 90};
  const size_t cantidadPasos = sizeof(pasos) / sizeof(pasos[0]);

  Serial.println(F("\n--- Iniciando prueba por pasos ---"));
  for (size_t i = 0; i < cantidadPasos; i++) {
    moverA(pasos[i]);
    delay(1000); // Pausa de 1 segundo para observar posicionamiento
  }
  Serial.println(F("--- Fin de la prueba por pasos ---\n"));
}

void procesarComandoSerie() {
  if (!Serial.available())
    return;

  String entrada = Serial.readStringUntil('\n');
  entrada.trim();
  if (entrada.length() == 0)
    return;

  char primerChar = entrada.charAt(0);

  if (primerChar == 'c' || primerChar == 'C') {
    modoBarrido = false;
    moverA(90);
  } else if (primerChar == 's' || primerChar == 'S') {
    modoBarrido = !modoBarrido;
    if (modoBarrido) {
      Serial.println(F("-> Barrido automático ACTIVADO. Envíe 's' o cualquier "
                       "ángulo para detenerlo."));
    } else {
      Serial.println(F("-> Barrido automático DETENIDO."));
    }
  } else if (primerChar == 'p' || primerChar == 'P') {
    modoBarrido = false;
    pruebaPorPasos();
  } else if (primerChar == '+') {
    modoBarrido = false;
    moverA(anguloActual + 5);
  } else if (primerChar == '-') {
    modoBarrido = false;
    moverA(anguloActual - 5);
  } else {
    // Intentar interpretar como número entero
    int angulo = entrada.toInt();
    if (entrada == "0" || angulo > 0) {
      modoBarrido = false;
      moverA(angulo);
    } else {
      Serial.println(F("Comando no reconocido."));
      imprimirMenu();
    }
  }
}

void actualizarBarridoAutomatico() {
  if (!modoBarrido)
    return;

  unsigned long ahora = millis();
  if (ahora - ultimoPasoBarrido >= INTERVALO_BARRIDO_MS) {
    ultimoPasoBarrido = ahora;

    anguloActual += incrementoBarrido;
    if (anguloActual >= ANGULO_MAX) {
      anguloActual = ANGULO_MAX;
      incrementoBarrido = -1;
    } else if (anguloActual <= ANGULO_MIN) {
      anguloActual = ANGULO_MIN;
      incrementoBarrido = 1;
    }
    servoRadar.write(anguloActual);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 2000)
    ; // Espera en placas nativas USB

  servoRadar.attach(PIN_SERVO);
  moverA(90); // Posición inicial de reposo al centro

  imprimirMenu();
}

void loop() {
  procesarComandoSerie();
  actualizarBarridoAutomatico();
}
