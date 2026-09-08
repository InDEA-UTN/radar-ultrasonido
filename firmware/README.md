# firmware/

Código de la parte que **mide**: dispara el sensor, cronometra el eco, mueve el servo y entrega los
pares *(ángulo, distancia)* con el formato de [`../docs/protocolo.md`](../docs/protocolo.md).

## Programas de prueba (Fase 2 — Componentes por separado)

Antes de integrar la adquisición completa, se encuentran los sketches de prueba unitaria:

| Directorio | Descripción | Conexión típica |
|---|---|---|
| [`test_sensor/`](test_sensor/test_sensor.ino) | Prueba de lectura y cálculo de distancia con el **HC-SR04** | `TRIG` -> Pin 11, `ECHO` -> Pin 12 |
| [`test_servo/`](test_servo/test_servo.ino) | Prueba de movimiento, barrido y calibración de límites/centro del **SG90** | `Señal` -> Pin 9 (PWM) |

## Firmware integrado (Fase 4)

Qué va acá depende de la [decisión de arquitectura](../docs/alternativas.md):

- **Opciones A y C** → un sketch de Arduino (`radar/radar.ino`). Nota práctica: la biblioteca
  `Servo` del Arduino usa el temporizador 1 y `pulseIn()` bloquea mientras espera el eco. Funcionan
  juntos, pero si aparecen mediciones inconsistentes vale la pena mirar ahí antes que en otro lado;
  la biblioteca `NewPing` evita parte del problema.
- **Opción B** → un módulo de Python sobre `pigpio` (no `RPi.GPIO`, por lo explicado en las
  alternativas), corriendo en la Raspberry.

Cuando esté definido el firmware final, este README detallará el proceso de compilación y carga.

