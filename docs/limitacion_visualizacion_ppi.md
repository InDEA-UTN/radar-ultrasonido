# Limitación Conocida: Superficies Planas con Apariencia Radial en el Display PPI

**Proyecto:** Radar de Ultrasonido InDEA — UTN FRM  
**Módulo afectado:** `host/radar_gui.py`, `host/radar_model.py`  
**Tipo:** Limitación de diseño inherente al sistema + característica del sensor  
**Estado:** Documentado, parcialmente mitigado. No es un bug del software.

---

## 1. Descripción del Fenómeno

Cuando el radar apunta a una **pared plana** (u otra superficie recta), la línea de contorno que traza la GUI sobre el display PPI **no aparece recta**, sino con una forma ligeramente curva o arqueada. Además, los bordes del contorno pueden verse **dentados o irregulares** (efecto "serrado").

Esto puede llevar a confundir la pared con una superficie convexa o cóncava cuando en realidad es plana.

> [!IMPORTANT]
> Este comportamiento **no es un bug del software**. Es la combinación de dos efectos independientes, ambos inherentes al hardware y al tipo de visualización elegido.

---

## 2. Causa 1 — Física del Display Polar (PPI)

### ¿Qué es un display PPI?

El software implementa un **Plan Position Indicator (PPI)**, el mismo tipo de visualización que usan los radares meteorológicos y militares. En este sistema:

- El **eje radial** representa la **distancia** al objeto.
- El **eje angular** representa el **ángulo** del servo.
- Cada punto se dibuja en coordenadas polares $(r, \theta)$ convertidas a píxeles con:

```
x = cx + r · cos(θ)
y = cy − r · sin(θ)
```

### ¿Por qué una pared plana se ve curva?

En coordenadas cartesianas, una pared plana tiene **distancia variable** según el ángulo de observación. Si la pared está perpendicular al eje de 90°, la distancia mínima se da a 90° y crece hacia los extremos siguiendo:

```
d(θ) = d_min / cos(θ − 90°)
```

En un display **cartesiano** (ejes XY fijos), conectar esos puntos da una línea perfectamente recta.  
En un display **polar** (ejes radiales), esos mismos puntos trazados y conectados generan una curva, porque la escala radial no es lineal respecto al espacio cartesiano.

```
Display Cartesiano         Display Polar (PPI)

  pared recta →            pared recta →
  ____________              ___ ___
 |            |           /         \      ← curva hacia adentro
 |            |          |           |
```

**Esto es el comportamiento correcto y esperado de cualquier radar PPI.** Todos los radares de este tipo, incluyendo los radares meteorológicos profesionales, presentan este efecto. Para verlo corregido habría que cambiar el tipo de visualización a una pantalla cartesiana (A-Scope o B-Scope), lo cual implicaría rediseñar completamente la GUI.

---

## 3. Causa 2 — Característica del Sensor HC-SR04

El sensor ultrasónico HC-SR04 tiene un **cono de detección de aproximadamente ±15°** alrededor de su eje. Esto significa que:

- A ángulos **oblicuos** respecto a una pared plana, el eco puede provenir de puntos distintos al que apunta el servo.
- Las reflexiones en superficies lisas a ángulo rasante son más débiles y menos consistentes.
- A ángulos oblicuos severos (por ejemplo, inclinaciones de 45°), la onda sufre **reflexión especular completa hacia un lateral**, impidiendo que el eco retorne al sensor y generando una pérdida total de detección (ver detalle en [`docs/limitacion_angulo_incidencia.md`](limitacion_angulo_incidencia.md)).
- Esto introduce **variaciones aleatorias de distancia** entre mediciones consecutivas, generando el efecto "dentado" o "serrado" en el contorno.

### Comparación de causas

| Efecto | Causa | ¿Evitable? |
|---|---|---|
| Contorno curvo en paredes planas | Geometría polar del display PPI | Solo cambiando a display cartesiano |
| Bordes dentados / irregulares | Ruido de reflexiones oblicuas del HC-SR04 | Parcialmente — ver Sección 4 |

---

## 4. Mitigación Implementada

Para reducir el efecto dentado (Causa 2), se implementó un **filtro de suavizado** en `radar_model.py`:

### Método `obtener_ecos_suavizados(ventana=3)`

Aplica una **media móvil ponderada triangular** sobre los ±`ventana` vecinos angulares de cada eco antes de graficar:

```python
peso(delta) = ventana + 1 − |delta|
dist_suavizada = Σ(dist[θ+δ] · peso(δ)) / Σ(peso(δ))
```

- **Ventana por defecto:** ±3° (7 muestras en total).
- **Los datos crudos del sensor no se modifican** — el suavizado solo se aplica en tiempo de render.
- Para ajustar la agresividad del filtro, modificar el parámetro `ventana` en las llamadas a `obtener_ecos_suavizados()` dentro de `radar_gui.py`:
  - `ventana=2` → más fiel al sensor, menos suave.
  - `ventana=5` → más suave, puede perder bordes abruptos de objetos pequeños.

> [!NOTE]
> El suavizado **no elimina la curvatura** del contorno (Causa 1), solo reduce la irregularidad dentada (Causa 2). Una pared plana seguirá viéndose ligeramente arqueada en el display PPI incluso con el filtro activo.

---

## 5. Recomendaciones para Futuros Desarrolladores

Si se desea eliminar completamente el efecto de curvatura, las alternativas son:

1. **Cambiar a visualización cartesiana (B-Scope):** Representar el eje X como el ángulo y el eje Y como la distancia. Las paredes planas se verían horizontales. Requiere rediseñar `_dibujar_grilla_polar` y `calcular_coordenadas_xy`.

2. **Corrección geométrica en tiempo real:** Convertir cada punto $(r, \theta)$ a cartesiano $(x_{cart}, y_{cart})$ y graficar sobre un canvas XY fijo. El display perdería la estética PPI circular pero las formas serían métricamente correctas.

3. **Sensor con menor ángulo de apertura:** Reemplazar el HC-SR04 por un sensor con cono de detección más estrecho (ej. JSN-SR04T, o sensores de tiempo de vuelo óptico como el VL53L1X) reduciría el ruido de reflexiones oblicuas.

4. **Aumentar la resolución angular del firmware:** Reducir el paso del servo (actualmente 1°) a 0.5° o usar un servo de mayor resolución permitiría al filtro de suavizado disponer de más muestras por grado, mejorando la calidad de la línea reconstruida.

---

## 6. Referencias

- *Understanding PPI Radar Displays*, Skolnik, M. — Introduction to Radar Systems, 3rd Ed.
- Datasheet HC-SR04: ángulo efectivo de detección ±15°, frecuencia 40 kHz.
- Documento complementario: [`docs/limitacion_angulo_incidencia.md`](limitacion_angulo_incidencia.md) — Pérdida de detección por ángulo de incidencia y reflexión especular.
- Código relacionado: [`host/radar_model.py`](../host/radar_model.py) · [`host/radar_gui.py`](../host/radar_gui.py)
