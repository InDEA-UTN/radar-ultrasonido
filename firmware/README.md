# firmware/

Código de la parte que **mide**: dispara el sensor, cronometra el eco, mueve el servo y entrega los
pares *(ángulo, distancia)* con el formato de [`../docs/protocolo.md`](../docs/protocolo.md).

Todavía vacío: qué va acá depende de la [decisión de arquitectura](../docs/alternativas.md).

- **Opciones A y C** → un sketch de Arduino (`radar/radar.ino`). Nota práctica: la biblioteca
  `Servo` del Arduino usa el temporizador 1 y `pulseIn()` bloquea mientras espera el eco. Funcionan
  juntos, pero si aparecen mediciones inconsistentes vale la pena mirar ahí antes que en otro lado;
  la biblioteca `NewPing` evita parte del problema.
- **Opción B** → un módulo de Python sobre `pigpio` (no `RPi.GPIO`, por lo explicado en las
  alternativas), corriendo en la Raspberry.

Cuando haya código, este README pasa a explicar cómo compilarlo y cargarlo.
