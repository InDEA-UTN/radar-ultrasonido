# Hardware

## Lo que ya tiene el laboratorio

Del [inventario de InDEA](https://github.com/InDEA-UTN) (repositorio de gestión, privado):

| Código | Ítem | Para qué |
|--------|------|----------|
| VELEZ 023 | Arduino Uno | Adquisición en las opciones A y C |
| VELEZ 026 | Raspberry Pi 3B+ (con microSD de 32 GB) | Opciones B y C |
| VELEZ 013 | Cables y jumpers | Conexionado |
| VELEZ 027 | Caja de componentes | Resistencias para el divisor, pines, protoboard |
| VELEZ 001 | Fuente de alimentación regulada | Alimentar el servo aparte |
| VELEZ 010 | Impresora 3D Creality | Soporte del cabezal |

## Lo que hay que comprar

| Componente | Cantidad | Nota |
|------------|----------|------|
| Sensor de ultrasonido HC-SR04 | 1 (idealmente 2) | El segundo, de repuesto: son baratos y se queman con un cortocircuito distraído |
| Micro servo SG90 | 1 (idealmente 2) | Vienen con los brazos plásticos y los tornillos |

Ambos son componentes de bajo costo y se consiguen en cualquier casa de electrónica de Mendoza o
por venta en línea.

## HC-SR04 — sensor de ultrasonido

Cuatro pines: `VCC` (**5 V**), `TRIG`, `ECHO`, `GND`.

Funciona así: se le da un pulso de **10 µs** en `TRIG`; el sensor emite una ráfaga de ocho ciclos a
40 kHz y pone `ECHO` en alto hasta que vuelve el eco. El ancho de ese pulso alto es el tiempo de
vuelo, ida y vuelta.

- Rango útil: **2 cm a 4 m**. Abajo de 2 cm miente.
- Haz de unos **15°**: no es un puntero láser. A 2 m "ve" un cono de más de medio metro de ancho, y
  el eco que vuelve es el del punto más cercano dentro de ese cono, no el del centro. Esto explica
  la mayoría de las lecturas raras.
- Superficies blandas (cortinas, ropa, gente abrigada) absorben el sonido y devuelven poco.
  Superficies en ángulo lo reflejan para otro lado y no vuelve nada.
- **Un disparo cada 60 ms como mínimo** (ver [`../docs/protocolo.md`](../docs/protocolo.md)).

### Con Arduino Uno

Directo: `VCC` a 5 V, `GND` a masa, `TRIG` y `ECHO` a dos pines digitales cualesquiera.

### Con Raspberry Pi 3B+ — atención

Los pines de la Raspberry toleran **3,3 V** y `ECHO` entrega **5 V**. Conectarlo directo daña el
pin. Hace falta un divisor resistivo:

```
ECHO ──[ R1 = 1 kΩ ]──┬── GPIO (entrada, 3,3 V)
                      │
                   [ R2 = 2 kΩ ]
                      │
                     GND
```

Con R1 = 1 kΩ y R2 = 2 kΩ, la entrada ve 5 V × 2/3 = **3,33 V**. Sirve igual R1 = 1 kΩ con
R2 = 1,8 kΩ (3,21 V) o dos resistencias de 1 kΩ en serie para armar los 2 kΩ.

`TRIG` sí puede ir directo desde un GPIO: el HC-SR04 reconoce los 3,3 V como nivel alto.

## SG90 — micro servo

Tres cables: rojo (**5 V**), marrón o negro (masa), naranja (señal).

- Se comanda con PWM (modulación por ancho de pulso) a **50 Hz**: un pulso de ~1 ms lo lleva a un
  extremo, ~2 ms al otro, ~1,5 ms al centro. Los extremos reales varían de unidad en unidad; hay
  que calibrarlos.
- Recorrido nominal 0°–180°, aunque en la práctica suele ser algo menos. **Forzarlo contra el tope
  lo hace zumbar y consumir de más**: conviene limitar por software a un rango seguro (por ejemplo
  10°–170°) hasta conocer la unidad.
- **Alimentación:** en el arranque y al frenar pega picos de varios cientos de miliamperios. Sacarlo
  del pin de 5 V del Arduino funciona a veces, y a veces provoca reinicios del microcontrolador en
  medio de una medición —una falla que hace perder mucho tiempo si no se la sospecha—. Lo correcto
  es alimentarlo de una **fuente aparte** (VELEZ 001) con la **masa unida** a la del
  microcontrolador. En la Raspberry esto no es opcional: es obligatorio.
- Un capacitor electrolítico de 100–470 µF entre 5 V y masa, cerca del servo, absorbe los picos.

## Soporte mecánico

El sensor va montado sobre el brazo del servo, con el eje del servo pasando por debajo del centro
del sensor para que el barrido sea limpio. Hay diseños libres para imprimir en 3D (buscar "HC-SR04
SG90 mount" o "ultrasonic radar bracket"), o se puede diseñar uno propio, que da la excusa perfecta
para usar la Creality del laboratorio.

Requisitos del soporte: que el sensor quede firme (si vibra, las lecturas bailan), que los cables
no traccionen del brazo del servo cuando gira, y que la base sea lo bastante pesada o esté sujeta
como para que el conjunto no se dé vuelta al frenar el servo.

## Conexionado

*(Completar con el esquema definitivo y una foto del montaje cuando esté armado.)*
