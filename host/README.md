# host/

Visualizador gráfico de radar tipo **PPI (Plan Position Indicator)** desarrollado en Python con **`pygame-ce`** y adquisición en tiempo real por puerto serie con **`pyserial`**.

Cumple con la especificación de comunicación definida en [docs/protocolo.md](../docs/protocolo.md).

---

## Estructura de archivos

- **[`main.py`](main.py):** Punto de entrada principal con opciones por línea de comandos.
- **[`lector_serie.py`](lector_serie.py):** Módulo de comunicación serie multihilo, no bloqueante y con autodetección de puertos.
- **[`radar_model.py`](radar_model.py):** Estructura de datos del barrido (0° a 180°), conversión polar/cartesiana y cálculo de persistencia de fósforo.
- **[`radar_gui.py`](radar_gui.py):** Motor gráfico en Pygame con pantalla PPI semicircular, estela de barrido, ecos con desvanecimiento alfa y panel HUD de telemetría.
- **[`simulador.py`](simulador.py):** Emulador virtual para pruebas visuales sin necesidad de hardware.
- **[`requirements.txt`](requirements.txt):** Dependencias de Python (`pyserial`, `pygame-ce`).

---

## Instalación de dependencias

```bash
# Crear y activar entorno virtual (opcional)
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r host/requirements.txt
```

---

## Modos de Ejecución

### 1. Lectura en Vivo por Puerto Serie (Arduino)
```bash
python3 host/main.py
```
*(Opcional: puedes especificar el puerto y baudrate)*:
```bash
python3 host/main.py -p /dev/ttyACM0 -b 115200
```

### 2. Modo Simulación Virtual (Sin Hardware)
Permite probar la interfaz gráfica y los efectos visuales inmediatamente:
```bash
python3 host/main.py --simular
```

---

## Controles en la Interfaz

| Tecla | Acción |
| :--- | :--- |
| `ESPACIO` | Pausar / Reanudar adquisición y barrido |
| `R` | Limpiar trazas / ecos históricos en pantalla |
| `+` / `↑` | Aumentar escala de alcance máximo (+500 mm) |
| `-` / `↓` | Reducir escala de alcance máximo (-500 mm) |
| `ESC` o `Q` | Cerrar la aplicación |
