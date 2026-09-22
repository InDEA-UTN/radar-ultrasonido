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

El sketch unificado que coordina el barrido del servo con la adquisición ultrasónica:

| Directorio | Descripción | Conexión típica |
|---|---|---|
| [`radar/`](radar/radar.ino) | Barrido coordinado ($0^\circ \leftrightarrow 180^\circ$) + medición y envío de telemetría por puerto serie (`115200` baud) | `Servo Signal` -> Pin 9, `TRIG` -> Pin 11, `ECHO` -> Pin 12 |

### Instrucciones de carga y prueba:
1. Abrir [`firmware/radar/radar.ino`](radar/radar.ino) en Arduino IDE.
2. Seleccionar la placa (ej. *Arduino Uno*) y el puerto serie correspondiente.
3. Compilar y subir el programa al microcontrolador.
4. Cerrar el Monitor Serie de Arduino IDE (para no bloquear el puerto) y ejecutar la interfaz gráfica en la computadora:
   ```bash
   python3 host/main.py
   ```


