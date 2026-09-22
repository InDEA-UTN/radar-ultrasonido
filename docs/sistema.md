# Radar de Ultrasonido — Documentación del Sistema Integrado

**Laboratorio InDEA** (Investigación y Desarrollo en Electrónica Aplicada)  
UTN Facultad Regional Mendoza  
*Responsable:* Gonzalo Luna — *Director:* Javier Velez

---

## 1. Visión General del Sistema

El sistema implementa un **radar de barrido acústico en tiempo real**. Un sensor ultrasónico **HC-SR04** montado sobre un servomotor **SG90** barre un sector angular de $180^\circ$, adquiere mediciones de distancia y las transmite por puerto serie USB hacia una computadora host, donde un software desarrollado en Python renderiza una pantalla tipo **PPI (Plan Position Indicator)** con estética táctica militar/laboratorio.

```
                  ┌──────────────────────────────┐
                  │      ARDUINO UNO (Fase 4)    │
                  │   firmware/radar/radar.ino   │
                  └──────┬────────────────┬──────┘
       PWM (Pin D9)      │                │ TRIG (D11) / ECHO (D12)
             ┌───────────▼──┐          ┌──▼──────────┐
             │  Servo SG90  │          │   HC-SR04   │
             │ (Barrido 180)│          │ (Ultrasonido)│
             └──────────────┘          └─────────────┘
                             │ USB Serie (115200 baud)
                             ▼
                  ┌──────────────────────────────┐
                  │    COMPUTADORA HOST (Fase 5) │
                  │       host/main.py           │
                  │  (Pygame-CE + PySerial)      │
                  └──────────────────────────────┘
```

---

## 2. Arquitectura de Hardware y Conexiones

Se seleccionó la **Arquitectura A** (adquisición determinista en microcontrolador y visualización en PC):

### 🔌 Pinout y Conexiones:

| Componente | Pin del Componente | Pin Arduino Uno | Función |
|---|---|---|---|
| **Micro Servo SG90** | Señal (Naranja / Amarillo) | **D9** (PWM) | Señal de control de posición angular |
| | VCC (Rojo) | **5V** (o fuente externa) | Alimentación positiva |
| | GND (Marrón / Negro) | **GND** | Masa de referencia común |
| **Sensor HC-SR04** | `TRIG` | **D11** | Disparo del pulso ultrasónico ($10\ \mu\text{s}$) |
| | `ECHO` | **D12** | Entrada del pulso de retorno |
| | `VCC` | **5V** | Alimentación positiva |
| | `GND` | **GND** | Masa común |

> [!IMPORTANT]
> **Recomendación eléctrica:** Si el servo presenta caídas de tensión o zumbidos en los topes, se recomienda alimentarlo con una fuente externa de 5V (GND unida a Arduino) y limitar el barrido a un rango seguro ($0^\circ \dots 180^\circ$).

---

## 3. Firmware Integrado (`firmware/radar/radar.ino`)

El firmware coordina el movimiento físico con la emisión y recepción ultrasónica en un bucle periódico parejo:

* **Sincronización:**
  1. El servo se posiciona en el `anguloActual` ($0^\circ \dots 180^\circ$).
  2. **Asentamiento mecánico:** Espera $25\text{ ms}$ para que el cabezal frene físicamente antes de medir.
  3. **Disparo ultrasónico:** Pulso de $10\ \mu\text{s}$ en `TRIG` y cronometraje con `pulseIn()` en `ECHO` (timeout $25\text{ ms}$).
  4. **Cálculo de distancia:** $d_{\text{mm}} = \frac{t_{\mu\text{s}} \cdot 10}{58}$ (calibrado a $20\ ^\circ\text{C}$).
  5. **Transmisión serie:** Emisión de la trama `<angulo>,<distancia_mm>,<estado>\n` a **115200 bps**.
  6. **Tiempo de guarda:** Pausa de $35\text{ ms}$ adicional para totalizar $\approx 60\text{ ms}$ por ciclo, disipando rebotes acústicos antes del siguiente disparo.
* **Comandos Serie Bidireccionales:** Admite control desde la PC (`'P'` pausa, `'S'` reanudar, `'Z'` volver a cero, `'C'` centrar a $90^\circ$).

---

## 4. Software de Visualización (`host/`)

El entorno en PC está modularizado en Python utilizando **`pygame-ce`** y **`pyserial`**:

### Módulos del Sistema:

1. **[`host/main.py`](../host/main.py):** Punto de entrada con argumentos de línea de comandos (`-p puerto`, `-b baudrate`, `--rango-max`, `--simular`).
2. **[`host/lector_serie.py`](../host/lector_serie.py):** Hilo de adquisición serie en segundo plano, no bloqueante, con cola de mensajes y autodetección de puertos (`/dev/ttyACM*`, `/dev/ttyUSB*`, `COM*`).
3. **[`host/radar_model.py`](../host/radar_model.py):**
   * Almacén de ecos en coordenadas polares.
   * Conversión a coordenadas cartesianas $(X, Y)$ de pantalla.
   * **Persistencia de fósforo:** Decaimiento suave $I(t) = (1 - \Delta t / \tau)^{1.2}$ con $\tau = 8.5\text{ s}$ para mantener la visualización completa durante el ciclo de ida y vuelta.
   * **Filtro de rango:** Descarte automático de detecciones fuera del rango observable ($40\text{ mm} \dots \text{rango\_max}$).
   * **Suavizado de ecos (`obtener_ecos_suavizados`):** Media móvil ponderada triangular sobre ±3 vecinos angulares aplicada en tiempo de render, sin modificar los datos crudos del sensor. Reduce el efecto dentado/serrado causado por reflexiones oblicuas del HC-SR04 en superficies planas.
4. **[`host/radar_gui.py`](../host/radar_gui.py):** Motor de renderizado PPI a 60 FPS:
   * **Grilla Polar:** Domo semicircular con marcas de distancia en cm/m y rayos angulares cada $15^\circ/30^\circ$.
   * **Efecto Linterna y Sombras Radiales:** Los obstáculos bloquean el haz y proyectan conos de sombra roja translúcida continua hacia el borde exterior.
   * **Superficie de Obstáculos:** Líneas de contorno frontales limpias en rojo brillante (`#FF4646`), sin puntos ni círculos.
   * **Bloqueo del Haz:** El haz verde se detiene en el punto de contacto del obstáculo.
   * **Panel HUD Lateral:** Lectura digital en tiempo real de ángulo, distancia en cm, barra de nivel, estado del enlace serie y atajos.
5. **[`host/simulador.py`](../host/simulador.py):** Generador sintético de barridos para pruebas y demostraciones completas sin conectar hardware.

---

## 5. Guía de Puesta en Marcha y Uso

### A. Preparación del Entorno (PC):
```bash
# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install -r host/requirements.txt
```

### B. Modo en Vivo con Hardware:
1. Abrir [`firmware/radar/radar.ino`](../firmware/radar/radar.ino) en Arduino IDE y cargarlo a la placa.
2. Cerrar el Monitor Serie de Arduino IDE para liberar el puerto.
3. Ejecutar la interfaz:
   ```bash
   python3 host/main.py
   ```

### C. Modo Simulación Virtual (Demostración):
```bash
python3 host/main.py --simular
```

---

## 6. Controles y Atajos de Teclado

| Tecla | Función |
| :--- | :--- |
| `ESPACIO` | **Pausar / Reanudar** la adquisición en pantalla |
| `R` | **Reiniciar / Limpiar** todos los ecos y sombras del mapa |
| `+` / `↑` | **Aumentar escala** máxima del radar (+250 mm) |
| `-` / `↓` | **Reducir escala** máxima del radar (-250 mm) |
| `ESC` o `Q` | **Salir** de la aplicación de manera segura |

---

## 7. Estado de las Fases del Proyecto

| Fase | Título | Estado | Evidencia / Código |
|---|---|---|---|
| **Fase 0** | Puesta en marcha | ✅ Completada | Repositorio y planteo inicial |
| **Fase 1** | Componentes y relevamiento | ✅ Completada | Lista de materiales y hardware verificado |
| **Fase 2** | Comprobación de componentes | ✅ Completada | [`test_sensor.ino`](../firmware/test_sensor/test_sensor.ino) y [`test_servo.ino`](../firmware/test_servo/test_servo.ino) |
| **Fase 3** | Elección de arquitectura | ✅ Completada | Arquitectura A seleccionada |
| **Fase 4** | Adquisición integrada | ✅ Completada | [`firmware/radar/radar.ino`](../firmware/radar/radar.ino) |
| **Fase 5** | Interfaz gráfica PPI | ✅ Completada | [`host/radar_gui.py`](../host/radar_gui.py) (Sombras radiales, HUD, filtrado, suavizado) |
| **Fase 6** | Cierre y documentación | 🔄 En curso | Soporte mecánico y documentación técnica |

---

## 8. Registro de Cambios (Changelog)

### Sesión 2026-09-09 — Mejoras Visuales de la GUI

| # | Cambio | Archivos afectados |
|---|---|---|
| 1 | **Estela de barrido translúcida:** el haz verde deja un rastro de desvanecimiento al barrer, similar a un tubo de rayos catódicos. | `radar_gui.py` |
| 2 | **Efecto linterna / sombra radial:** los obstáculos detectados proyectan un cono de sombra desde el punto de eco hasta el borde del radar, imitando el efecto de una linterna. Inicialmente oscuro, luego cambiado a rojo translúcido por mejor contraste. | `radar_gui.py` |
| 3 | **Sombra uniforme sin solapamientos:** se reemplazó el enfoque de múltiples polígonos individuales por un único polígono continuo por cluster de ecos contiguos, eliminando las bandas oscuras por solapamiento de alfa. | `radar_gui.py` |
| 4 | **Filtro de rango observable:** las mediciones fuera del rango configurado (`rango_min` … `rango_max`) se descartan silenciosamente y no se grafican ni como eco ni como sombra. | `radar_model.py` |
| 5 | **Eliminación de punto de impacto y círculos:** se eliminaron el punto rojo que seguía al haz y los círculos de impacto para una visualización más limpia, mostrando solo la línea de contorno frontal del obstáculo. | `radar_gui.py` |

### Sesión 2026-09-15 — Suavizado de Mediciones

| # | Cambio | Archivos afectados |
|---|---|---|
| 1 | **Análisis del efecto dentado:** se diagnosticó que la apariencia curva/irregular de superficies planas en el display PPI es una combinación de la física inherente del radar polar (no corregible sin cambiar el tipo de display) y del ruido de reflexiones oblicuas del HC-SR04 (reducible por software). | — |
| 2 | **Suavizado con media móvil triangular (`obtener_ecos_suavizados`):** nuevo método en `radar_model.py` que calcula la distancia suavizada de cada eco usando los ±3 vecinos angulares con pesos triangulares. Los datos crudos del sensor se conservan intactos en `self.ecos`. | `radar_model.py` |
| 3 | **Integración del suavizado en el render:** `_dibujar_ecos` y `_dibujar_sombras` en la GUI ahora consumen `obtener_ecos_suavizados()` en lugar de `obtener_ecos_activos()`. | `radar_gui.py` |

---

## 9. Documentos Técnicos Relacionados

| Documento | Descripción |
|---|---|
| [`limitacion_visualizacion_ppi.md`](./limitacion_visualizacion_ppi.md) | Explica por qué las superficies planas se ven con apariencia curva en el display PPI: causas físicas, mitigación implementada y recomendaciones para futuros desarrolladores. |
| [`limitacion_angulo_incidencia.md`](./limitacion_angulo_incidencia.md) | Detalla la limitación física por reflexión especular y pérdida de detección en superficies planas oblicuas (inclinaciones a 45°), cono del HC-SR04 y directrices de ensayo. |


