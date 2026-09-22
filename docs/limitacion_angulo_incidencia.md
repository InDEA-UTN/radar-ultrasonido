# Limitación Física: Pérdida de Detección por Ángulo de Incidencia y Reflexión Especular

**Proyecto:** Radar de Ultrasonido InDEA — UTN FRM  
**Módulo afectado:** Sensor ultrasónico HC-SR04 (Hardware acústico)  
**Tipo:** Limitación física fundamental de la acústica ondulatoria  
**Estado:** Documentado. Fenómeno físico no corregible por software.

---

## 1. Descripción del Fenómeno

Durante las pruebas experimentales del radar acústico se observa que:
* **Superficies planas perpendiculares** al eje del sensor (ángulo de incidencia $\approx 0^\circ$) se detectan con alta precisión y consistencia.
* **Superficies planas lisas inclinadas** a ángulos pronunciados (por ejemplo, $45^\circ$ respecto al haz del sensor) **no son detectadas** en absoluto o producen lecturas esporádicas e incoherentes.

El sensor se comporta como si el objeto no existiera frente a él, dejando un "hueco" o zona vacía en el display PPI.

> [!IMPORTANT]
> Este comportamiento **no es un fallo del sensor HC-SR04, ni un error del firmware en Arduino, ni un bug en la GUI**. Se trata de un fenómeno físico intrínseco de la **reflexión especular de ondas acústicas** en combinación con la geometría del cono de recepción.

---

## 2. Fundamento Físico

### 2.1. Longitud de Onda Acústica del HC-SR04
El sensor opera emitiendo una ráfaga de 8 pulsos ultrasónicos a una frecuencia fija de $f = 40\text{ kHz}$. A una temperatura ambiente de $20^\circ\text{C}$ (velocidad del sonido $c \approx 343\text{ m/s}$), la longitud de onda ($\lambda$) en el aire es:

$$\lambda = \frac{c}{f} = \frac{343\text{ m/s}}{40\,000\text{ Hz}} \approx 8.57\text{ mm}$$

### 2.2. Reflexión Especular vs. Reflexión Difusa
La forma en que la onda rebota en un obstáculo depende de la relación entre la longitud de onda ($\lambda$) y las rugosidades de la superficie ($R$):

1. **Reflexión Especular ($R \ll \lambda$):**  
   Si la superficie es lisa en comparación con $8.5\text{ mm}$ (cartón, madera pulida, acrílico, vidrio, chapa, paredes revocadas lisas), la onda acústica se comporta idénticamente a un haz de luz frente a un espejo plano, cumpliendo la **Ley de Reflexión de Snell**:
   $$\theta_i = \theta_r$$
   El ángulo de reflexión respecto a la normal de la superficie es exactamente igual al ángulo de incidencia.

2. **Reflexión Difusa o Scattering ($R \ge \lambda$):**  
   Si la superficie presenta irregularidades de escala similar o mayor a $8.5\text{ mm}$ (piedras, telas rugosas, esponjas porosas, vegetación), la energía acústica se dispersa en todas las direcciones, permitiendo que una fracción de la onda regrese hacia el sensor emisor.

```
Reflexión Especular (Lisas, R << λ)         Reflexión Difusa (Rugosas, R >= λ)
         Normal                                      Normal
           │                                           │
  Incidente│Reflejada                         Incidente│ Dispersión
     \     │     /                               \     │ /  ↑  \
      \ θi │ θr /                                 \    │/   │   \
───────\───┴───/───────                     ───────\───┴─────────────
   Superficie Lisa                             Superficie Rugosa
```

---

## 3. Análisis Geométrico a 45° de Inclinación

### Caso A: Superficie Perpendicular (Detección Óptima)
Cuando el haz incide perpendicularmente a la superficie plana ($\theta_i = 0^\circ$):
* La onda se refleja directamente hacia atrás sobre su propio eje ($\theta_r = 0^\circ$).
* El transductor receptor (Rx) recibe el eco de máxima energía.

### Caso B: Superficie Inclinada a 45° (Pérdida Total de Eco)
Cuando una superficie plana lisa está orientada a $45^\circ$ respecto a la trayectoria del pulso:
* El ángulo respecto a la normal de la superficie es $\theta_i = 45^\circ$.
* El ángulo de rebote es $\theta_r = 45^\circ$.
* El ángulo total de deflexión respecto a la trayectoria original es:
  $$\Delta\alpha = 180^\circ - 2\cdot(90^\circ - 45^\circ) = 90^\circ$$
* La onda reflejada sale despedida **hacia un lateral a $90^\circ$**, viajando en dirección ortogonal al sensor y alejándose definitivamente del transductor receptor (Rx).

```
                      SUPERFICIE A 45°
                          /
                         /  Superficie
                        /   plana
                       /
                      /
    Pulso Emitido    / 
    ───────────────>●  Punto de impacto
                   /│ 
                  / │ 
                 /  │ Pulso Reflejado (Desvío 90°)
                /   │ 
                    │
                    ▼  (Viaja lejos del sensor)

    ┌─────────┐
    │ Tx   Rx │   Sensor HC-SR04
    └─────────┘
```

---

## 4. Cono de Apertura del Sensor HC-SR04 y Ángulo Límite

El transductor piezoeléctrico del HC-SR04 tiene un **cono de haz de aproximadamente $\pm 15^\circ$** respecto a su eje central (apertura total de unos $30^\circ$).

* Para que el transductor Rx pueda captar un eco útil de una superficie plana lisa, la inclinación de la superficie respecto a la perpendicular **no debe superar aproximadamente los $10^\circ \dots 15^\circ$**.
* Con inclinaciones superiores a $15^\circ$ (y dramáticamente a $45^\circ$), la energía que retrodispersa hacia el receptor es prácticamente nula (atenuación superior a $40\text{ dB}$, por debajo del umbral de detección del comparador del HC-SR04).

---

## 5. Efectos Observables en el Sistema

| Fenómeno en Hardware | Comportamiento en Firmware / Serie | Representación en GUI (Display PPI) |
|---|---|---|
| **Pérdida de eco por deflexión** | El pin ECHO no detecta pulso de retorno y vence el tiempo límite (`pulseIn` timeout). El firmware reporta `0 cm` o distancia fuera de rango. | No se dibuja ningún blanco en ese ángulo. Se genera un "hueco" en la detección de la pared. |
| **Rebote multitrayecto (Multipath)** | El pulso desviado a $90^\circ$ rebota en una segunda o tercera pared antes de volver al receptor con retardo elevado. | Se grafican ecos "fantasma" a distancias considerablemente mayores que la real. |

---

## 6. Analogía: Principio de Tecnología Furtiva (*Stealth*)

Este fenómeno físico es exactamente la base utilizada por las aeronaves de combate de baja observabilidad (como el **Lockheed F-117 Nighthawk** o el **B-2 Spirit**):

* En lugar de emplear superficies curvas que siempre presentan algún punto perpendicular al radar enemigo, están construidas con **paneles planos fuertemente facetados e inclinados** (comúnmente a $45^\circ$ o más).
* De este modo, las ondas de radio incidentes emitidas por un radar monostático rebotan hacia el espacio o hacia el suelo, impidiendo que la energía regrese a la antena receptora.

---

## 7. Directrices Prácticas para Pruebas y Ensayos

Para validar el sistema y evitar falsos diagnósticos de falla:

1. **Uso de blancos de prueba adecuados:**
   * Al ensayar la precisión del radar con obstáculos aislados, preferir **cuerpos cilíndricos** (botellas, tubos de PVC, latas) o **esféricos**. Los cilindros y esferas siempre ofrecen una generatriz o punto perpendicular a la línea de visión del sensor, sin importar el ángulo de barrido.
2. **Orientación de paredes y paneles:**
   * Las paredes de prueba deben posicionarse lo más perpendiculares posible a la línea de mira central ($90^\circ$). En los extremos del barrido ($0^\circ$ y $180^\circ$), una pared recta frontal tendrá naturalmente un ángulo oblicuo elevado, por lo que es normal que los extremos presenten pérdida de eco.
3. **Alternativa en hardware para aplicaciones avanzadas:**
   * Si la aplicación requiere detectar superficies planas fuertemente inclinadas, se debe recurrir a **fusión sensorial**:
     * Sensores ópticos de tiempo de vuelo (ToF como el VL53L1X), cuya dispersión óptica superficial es diferente.
     * Arreglos multirreceptores (radar bi-estático o multi-sensor), donde receptores adyacentes captan los ecos desviados lateralmente.

---

## 8. Referencias Cruzadas

* [`docs/limitacion_visualizacion_ppi.md`](limitacion_visualizacion_ppi.md) — Efecto de curvatura radial y bordes dentados en display polar.
* [`docs/sistema.md`](sistema.md) — Arquitectura de hardware y especificaciones del HC-SR04.
