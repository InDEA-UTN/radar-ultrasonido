# Alternativas de arquitectura

> **Estado: sin decidir.** Este documento plantea las opciones y cómo elegir entre ellas. Cuando la
> decisión esté tomada, se escribe al final, en la sección [Decisión](#decisión), con el motivo y
> los datos que la respaldan.

El proyecto tiene dos mitades —**adquisición** (medir) e **interfaz** (mostrar)— y el laboratorio
tiene dos plataformas donde ponerlas: un **Arduino Uno** y una **Raspberry Pi 3B+**. De ahí salen
las tres combinaciones que valen la pena.

---

## A. Arduino mide, la PC muestra

El Arduino Uno dispara el HC-SR04, mide el ancho del pulso de eco, mueve el SG90 un paso y manda
por el puerto serie (USB) una línea con el ángulo y la distancia. En la PC, un programa —Python es
lo natural: `pyserial` para leer y PyQt, `pygame` o `matplotlib` para dibujar— arma la pantalla PPI.

**A favor**

- La medición del eco la hace un microcontrolador que no tiene sistema operativo interrumpiéndolo:
  el tiempo que mide es el que ocurrió, sin que el planificador de tareas le robe el reloj.
- El PWM del servo es estable por hardware.
- Separa limpio el firmware de la interfaz. Se puede trabajar en una mitad sin romper la otra, y
  cada mitad se prueba por separado (el firmware con el monitor serie, la interfaz con datos
  grabados en un archivo).
- Es la configuración más documentada del mundo: si algo se traba, hay mil referencias.

**En contra**

- Necesita una PC atada por el cable USB. El radar no funciona solo.
- El Uno tiene 2 KB de memoria RAM (memoria de acceso aleatorio): no hay lugar para guardar
  historial ni procesar mucho a bordo. No es un problema real acá, pero es el techo.

## B. La Raspberry hace todo

La Raspberry Pi 3B+ maneja el sensor y el servo directamente por sus pines GPIO (entrada/salida de
propósito general), y en la misma placa corre el programa que dibuja, con un monitor conectado.

**A favor**

- Una sola plataforma, un solo lenguaje, un solo programa. Menos piezas.
- No hace falta una PC: la Raspberry *es* la computadora.
- Todo el poder de Linux a mano: guardar los barridos en archivos, procesarlos con `numpy`,
  graficarlos.

**En contra**

- **Este es el punto crítico del proyecto.** Linux no es un sistema operativo de tiempo real:
  entre que llega el flanco de subida del eco y que el programa lo registra, el sistema puede
  haberse ido a atender otra cosa. Esa demora variable —*jitter*— se traduce en centímetros de
  error que aparecen y desaparecen sin motivo aparente. Con la biblioteca `pigpio`, que muestrea
  los pines por DMA (acceso directo a memoria) a 1 MHz, mejora bastante; con `RPi.GPIO` leyendo en
  un bucle de Python, es malo.
- El PWM del servo tiene el mismo problema: por software tiembla, y el temblor se ve como un
  micro-vibrado del cabezal. `pigpio` también lo resuelve.
- El HC-SR04 entrega el eco a 5 V y los pines de la Raspberry toleran **3,3 V**. Sin un divisor
  resistivo, el pin se daña. Ver [`../hardware/README.md`](../hardware/README.md).

## C. Arduino mide, la Raspberry sirve una interfaz web

El Arduino hace exactamente lo mismo que en la opción A, pero el cable USB va a la Raspberry en vez
de a la PC. La Raspberry corre un servidor web —FastAPI o Flask, empujando los datos por WebSocket—
y la pantalla PPI se dibuja en el navegador, sobre un `canvas`. El radar se ve desde el celular o
desde cualquier máquina de la red.

**A favor**

- Conserva la calidad de medición de la opción A: el que mide sigue siendo el microcontrolador.
- El radar queda autónomo: enchufado a la corriente, sin monitor, sin PC, accesible por la red.
- Es la versión más vistosa para mostrar en una demostración o una jornada de puertas abiertas.

**En contra**

- Es la que más piezas tiene: firmware, servidor y cliente web. Más superficie donde algo falle.
- Suma temas que no son del proyecto en sí: red, direcciones IP, arranque automático del servicio.

**Observación importante:** C **no compite** con A, la continúa. Si el formato de los datos que
manda el Arduino queda bien definido (ver [`protocolo.md`](protocolo.md)), pasar de A a C es
cambiar de lugar el extremo del cable y escribir la interfaz nueva. El firmware no se toca.

---

## Criterios para decidir

En orden de peso para este proyecto:

1. **Calidad de la medición.** Un radar que informa 47 cm cuando la pared está a 50 cm, y 52 cm en
   la medición siguiente, no es un radar: es un generador de números. Es el criterio que manda.
2. **Que se pueda depurar.** Cuando algo no funcione —y algo no va a funcionar—, ¿se puede aislar
   la parte culpable y probarla sola?
3. **Costo y disponibilidad.** Las tres usan equipo que ya está en el laboratorio; lo único que hay
   que comprar es el sensor y el servo. No debería inclinar la balanza.
4. **Lo que se aprende.** Las tres enseñan cosas distintas: A y C, la separación entre el mundo de
   tiempo real y el mundo del sistema operativo; B, cuánto duele no tener tiempo real.
5. **Cómo se muestra.** Si el destino es una demostración pública, C gana por lejos.

## El experimento que decide

Antes de elegir por intuición, conviene medir. La prueba es corta y da un número:

1. Poner el sensor fijo, apuntando perpendicular a una pared lisa, a una distancia conocida y
   medida con cinta métrica (50 cm anda bien).
2. Tomar **200 mediciones seguidas**, a unas 10 por segundo, sin mover nada.
3. Calcular el promedio, la desviación estándar y el valor mínimo y máximo.
4. Repetir lo mismo en cada plataforma candidata: Arduino con `pulseIn()`, Raspberry con `pigpio`,
   y —si se quiere ver el contraste— Raspberry con `RPi.GPIO` en un bucle de Python.

La desviación estándar es la respuesta. Si en la Raspberry es varias veces más grande que en el
Arduino, la opción B queda descartada por sí sola y no hace falta discutirlo más. Si es comparable,
B entra en juego con todas las de la ley.

Los datos crudos y las conclusiones de este experimento se guardan en `docs/` (por ejemplo,
`docs/experimento_jitter.md` más los archivos de mediciones) y se citan en la decisión.

---

## Decisión

*(Pendiente. Cuando esté tomada, completar acá: qué se eligió, con qué números o argumentos, y qué
queda como línea abierta para más adelante.)*

- **Arquitectura elegida:** —
- **Fecha:** —
- **Motivo:** —
- **Qué queda pendiente de investigar:** —
