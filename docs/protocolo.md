# Protocolo de datos entre la adquisición y la interfaz

> **Propuesta, sujeta a la [decisión de arquitectura](alternativas.md).** Si la adquisición y la
> interfaz terminan viviendo en el mismo programa (opción B), este documento se vuelve innecesario;
> si están separadas (opciones A y C), es la pieza que las mantiene independientes.

El valor de fijar el formato temprano es que permite escribir y probar la interfaz **sin tener el
hardware delante**: se le da un archivo con barridos grabados y dibuja igual.

## Enlace

Puerto serie sobre USB, **115200 baudios, 8N1**, sin control de flujo. A 115200 una línea de ~15
caracteres tarda poco más de un milisegundo: sobra para un barrido de 180 pasos.

## De la adquisición hacia la interfaz

Texto ASCII, una medición por línea, terminada en `\n`:

```
<angulo>,<distancia>,<estado>
```

- `angulo` — entero, grados, 0 a 180.
- `distancia` — entero, **milímetros**. Enteros en milímetros y no decimales en centímetros: evita
  discutir con el separador decimal y no pierde resolución (el HC-SR04 no da más de ~3 mm útiles).
- `estado` — `0` medición válida, `1` sin eco / fuera de rango, `2` eco descartado por el filtro.

Ejemplo de un tramo de barrido:

```
88,1240,0
89,1237,0
90,0,1
91,1198,0
```

Las líneas que empiezan con `#` son comentarios o mensajes de diagnóstico y la interfaz las ignora
o las muestra en un panel aparte. Al arrancar conviene emitir una cabecera:

```
# radar-ultrasonido v0.1 paso=1 periodo_ms=60 rango_mm=40..4000
```

## De la interfaz hacia la adquisición *(opcional)*

Comandos de una letra, terminados en `\n`. Si complican el firmware, se dejan para más adelante:

| Comando | Efecto |
|---------|--------|
| `S` | Iniciar el barrido |
| `P` | Pausar |
| `Z` | Volver a 0° |
| `?` | Reenviar la cabecera |

## Detalles que importan

- **Ritmo.** El HC-SR04 necesita unos **60 ms entre disparos**: si se lo apura, el eco del disparo
  anterior todavía anda dando vueltas por la sala y se lo confunde con el nuevo. Un barrido de 180°
  con paso de 1° lleva entonces unos 11 segundos; con paso de 2°, unos 5,5. La velocidad del
  barrido se ajusta con el paso, no acortando el período.
- **Asentamiento del servo.** Después de ordenarle un ángulo, el SG90 tarda en llegar. Medir antes
  de que se haya asentado devuelve la distancia de un ángulo que ya no es el que se informa. Hay
  que esperar (del orden de 15–30 ms para un paso chico) y dejarlo escrito en el código.
- **Sin eco.** Cuando no vuelve nada, el sensor deja el pin de eco arriba hasta el vencimiento del
  plazo (unos 38 ms). Eso **no** es distancia máxima: es "no sé". Por eso existe el campo de
  estado, y por eso la interfaz no debe dibujar un obstáculo a 4 metros cuando en realidad no vio
  nada.
- **Cálculo de la distancia.** Con el tiempo de vuelo `t` en microsegundos y la velocidad del
  sonido `c` en m/s: `distancia_mm = t * c / 2000`. A 20 °C, `c ≈ 343 m/s`, lo que da la fórmula
  conocida `d_cm ≈ t_us / 58`. La velocidad depende de la temperatura
  (`c ≈ 331,4 + 0,6 · T[°C]`): entre 5 °C y 35 °C hay un 5 % de diferencia, que a 2 metros son
  10 cm. Si se busca precisión, hay que medir la temperatura.
