#!/usr/bin/env python3
"""
lector_serie.py

Módulo para la adquisición de datos del radar ultrasónico a través del puerto serie.
Implementa el protocolo especificado en docs/protocolo.md:
  - Formato de línea: <angulo>,<distancia_mm>,<estado>
  - Baudrate por defecto: 115200 (8N1)
  - Líneas que inician con '#' son comentarios/diagnóstico.
"""

import time
import threading
import queue
from dataclasses import dataclass
from typing import Optional, List, Callable
import serial
import serial.tools.list_ports


@dataclass
class Medicion:
    angulo: int          # 0 a 180 grados
    distancia_mm: int    # distancia en milímetros
    estado: int          # 0: Válida, 1: Sin eco / fuera de rango, 2: Filtrado
    timestamp: float     # tiempo local en segundos (time.time())

    @property
    def distancia_cm(self) -> float:
        return self.distancia_mm / 10.0

    @property
    def es_valida(self) -> bool:
        return self.estado == 0 and self.distancia_mm > 0


def listar_puertos_disponibles() -> List[str]:
    """Retorna una lista con los nombres de los puertos serie detectados."""
    puertos = serial.tools.list_ports.comports()
    return [p.device for p in puertos]


def autodetectar_puerto_arduino() -> Optional[str]:
    """Intenta encontrar un puerto asociado a Arduino o el primer puerto serie USB disponible."""
    puertos = serial.tools.list_ports.comports()
    for p in puertos:
        desc = (p.description or "").lower()
        mfg = (p.manufacturer or "").lower()
        if "arduino" in desc or "arduino" in mfg or "ch340" in desc or "ftdi" in desc:
            return p.device

    # Si no encuentra coincidencia explícita, devolver el primer ttyACM o ttyUSB
    for p in puertos:
        if "ttyACM" in p.device or "ttyUSB" in p.device:
            return p.device

    return puertos[0].device if puertos else None


class LectorSerie:
    def __init__(
        self,
        puerto: Optional[str] = None,
        baudrate: int = 115200,
        timeout: float = 0.5,
        on_comentario: Optional[Callable[[str], None]] = None
    ):
        self.puerto_configurado = puerto
        self.baudrate = baudrate
        self.timeout = timeout
        self.on_comentario = on_comentario

        self._ser: Optional[serial.Serial] = None
        self._cola_mediciones: queue.Queue[Medicion] = queue.Queue(maxsize=1000)
        self._hilo: Optional[threading.Thread] = None
        self._ejecutando = False
        self._conectado = False
        self._ultimo_error = ""

    @property
    def conectado(self) -> bool:
        return self._conectado and self._ser is not None and self._ser.is_open

    @property
    def ultimo_error(self) -> str:
        return self._ultimo_error

    def iniciar(self) -> bool:
        """Inicia el hilo lector en segundo plano."""
        if self._ejecutando:
            return True

        self._ejecutando = True
        self._hilo = threading.Thread(target=self._bucle_lectura, daemon=True)
        self._hilo.start()
        return True

    def detener(self):
        """Detiene el lector y cierra el puerto serie."""
        self._ejecutando = False
        self._cerrar_puerto()
        if self._hilo and self._hilo.is_alive():
            self._hilo.join(timeout=1.0)

    def _conectar(self) -> bool:
        puerto = self.puerto_configurado or autodetectar_puerto_arduino()
        if not puerto:
            self._ultimo_error = "No se encontraron puertos serie disponibles."
            self._conectado = False
            return False

        try:
            self._ser = serial.Serial(
                port=puerto,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            # Pequeña pausa para permitir el reinicio de Arduino tras DTR toggle
            time.sleep(0.1)
            self._ser.reset_input_buffer()
            self._conectado = True
            self._ultimo_error = ""
            print(f"[LectorSerie] Conectado exitosamente a {puerto} a {self.baudrate} baudios.")
            return True
        except serial.SerialException as e:
            self._ultimo_error = f"Error al abrir {puerto}: {e}"
            self._conectado = False
            self._ser = None
            return False

    def _cerrar_puerto(self):
        self._conectado = False
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    def _bucle_lectura(self):
        while self._ejecutando:
            if not self.conectado:
                if not self._conectar():
                    time.sleep(1.5)  # Reintentar cada 1.5s
                    continue

            try:
                linea_raw = self._ser.readline()
                if not linea_raw:
                    continue

                linea = linea_raw.decode('utf-8', errors='ignore').strip()
                if not linea:
                    continue

                # Líneas de comentario / diagnóstico
                if linea.startswith('#'):
                    if self.on_comentario:
                        self.on_comentario(linea)
                    else:
                        print(f"[Arduino #] {linea}")
                    continue

                # Parsear medición: <angulo>,<distancia_mm>,<estado>
                partes = linea.split(',')
                if len(partes) >= 3:
                    try:
                        angulo = int(partes[0].strip())
                        distancia_mm = int(partes[1].strip())
                        estado = int(partes[2].strip())

                        medicion = Medicion(
                            angulo=angulo,
                            distancia_mm=distancia_mm,
                            estado=estado,
                            timestamp=time.time()
                        )

                        # Insertar en cola no bloqueante descartando las más viejas si está llena
                        if self._cola_mediciones.full():
                            try:
                                self._cola_mediciones.get_nowait()
                            except queue.Empty:
                                pass

                        self._cola_mediciones.put_nowait(medicion)
                    except ValueError:
                        # Formato inesperado en los números
                        pass

            except serial.SerialException as e:
                self._ultimo_error = f"Error de comunicación serie: {e}"
                print(f"[LectorSerie] Desconectado: {e}")
                self._cerrar_puerto()
                time.sleep(1.0)
            except Exception as e:
                self._ultimo_error = f"Error inesperado: {e}"
                time.sleep(0.1)

    def obtener_mediciones(self) -> List[Medicion]:
        """Extrae todas las nuevas mediciones acumuladas en la cola."""
        mediciones = []
        while not self._cola_mediciones.empty():
            try:
                mediciones.append(self._cola_mediciones.get_nowait())
            except queue.Empty:
                break
        return mediciones

    def enviar_comando(self, comando: str) -> bool:
        """Envía un comando de una letra o texto a Arduino."""
        if not self.conectado or not self._ser:
            return False
        try:
            texto = comando.strip() + '\n'
            self._ser.write(texto.encode('utf-8'))
            self._ser.flush()
            return True
        except serial.SerialException as e:
            self._ultimo_error = f"Error al enviar comando: {e}"
            return False
