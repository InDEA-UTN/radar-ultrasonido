# Plan de trabajo

Las fases son una guía, no un contrato: si el proyecto pide reordenarlas, se reordenan y se anota
acá el porqué.

## Estado actual

**Fase 1** — relevamiento y compra de los componentes que faltan.

## Fases

### Fase 0 — Puesta en marcha *(hecha)*

Repositorio creado, planteo del problema escrito, alternativas descritas.

### Fase 1 — Componentes

Conseguir el HC-SR04 y el SG90 (ver [`../hardware/README.md`](../hardware/README.md)) y verificar
que el Arduino Uno del laboratorio (VELEZ 023) y la Raspberry Pi 3B+ (VELEZ 026) arrancan.

### Fase 2 — Cada pieza por separado

Antes de integrar nada, probar los dos componentes por su cuenta:

- **Sensor:** medir la distancia a un objeto fijo y comparar con la cinta métrica. Entender la
  fórmula del tiempo de vuelo y el efecto de la temperatura.
- **Servo:** barrer de 0° a 180° y volver, y verificar que la posición se corresponde con el ángulo
  pedido. Marcar los topes reales del servo, que rara vez son exactamente 0 y 180.

Que las dos piezas anden por separado antes de juntarlas ahorra horas de buscar el error en el
lugar equivocado.

### Fase 3 — Elegir la arquitectura

Correr el experimento de [`alternativas.md`](alternativas.md), comparar los números, decidir y
dejarlo escrito. Sin fecha límite: la decisión se toma cuando haya datos que la sostengan.

### Fase 4 — Adquisición integrada

Barrido completo entregando pares *(ángulo, distancia)* a ritmo parejo, con el formato de
[`protocolo.md`](protocolo.md). El criterio para dar la fase por cerrada es poder grabar un barrido
en un archivo y que los números tengan sentido.

### Fase 5 — Interfaz gráfica

Pantalla PPI: sectores, marcas de distancia, la línea de barrido y las trazas desvaneciéndose.
Primero funciona con datos grabados, después en vivo.

### Fase 6 — Cierre

Soporte mecánico definitivo, documentación de uso, fotos y un video corto del radar funcionando.

## Ideas para después

Cosas que no son del alcance inicial pero que el proyecto habilita:

- Corrección de la velocidad del sonido por temperatura, con un sensor DHT22 o similar.
- Barrer también en elevación con un segundo servo (radar de dos ejes).
- Detección de objetos en movimiento comparando barridos consecutivos.
- Registro histórico de barridos y reproducción posterior.
