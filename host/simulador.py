#!/usr/bin/env python3
"""
simulador.py

Generador sintético de barridos de radar para pruebas de la interfaz gráfica
sin necesidad de tener el hardware físico conectado.
Emula el comportamiento y tiempos del servomotor SG90 y sensor HC-SR04.
"""

import time
import math
import queue
import threading
from typing import List, Optional
from lector_serie import Medicion


class LectorSimulado:
    """Emulador de LectorSerie que produce mediciones sintéticas en tiempo real."""

    def __init__(self, paso_grados: int = 1, periodo_paso_s: float = 0.04):
        self.paso_grados = paso_grados
        self.periodo_paso_s = periodo_paso_s
        self.puerto_configurado = "MODO SIMULADOR VIRTUAL"

        self._cola: queue.Queue[Medicion] = queue.Queue(maxsize=1000)
        self._hilo: Optional[threading.Thread] = None
        self._ejecutando = False
        self._conectado = True
        self._ultimo_error = ""

    @property
    def conectado(self) -> bool:
        return self._conectado

    @property
    def ultimo_error(self) -> str:
        return self._ultimo_error

    def iniciar(self) -> bool:
        if self._ejecutando:
            return True
        self._ejecutando = True
        self._hilo = threading.Thread(target=self._bucle_simulacion, daemon=True)
        self._hilo.start()
        return True

    def detener(self):
        self._ejecutando = False
        if self._hilo and self._hilo.is_alive():
            self._hilo.join(timeout=1.0)

    def _bucle_simulacion(self):
        angulo = 0
        direccion = 1

        while self._ejecutando:
            # Simular obstáculos en el espacio virtual:
            # 1. Obstáculo cercano a los 40° - 55° (distancia ~700 mm con leve ruido)
            # 2. Obstáculo mediano a los 115° - 140° (distancia ~1350 mm)
            # 3. Obstáculo móvil a los 85° - 95°
            t = time.time()
            distancia_mm = 0
            estado = 1  # Por defecto sin eco

            if 40 <= angulo <= 55:
                # Obstáculo fijo 1 (a 70 cm / 700 mm)
                distancia_mm = 700
                estado = 0
            elif 120 <= angulo <= 145:
                # Obstáculo fijo 2 (a 45 cm / 450 mm)
                distancia_mm = 450
                estado = 0
            elif 80 <= angulo <= 100:
                # Obstáculo móvil / dinámico acercándose y alejándose suavemente (entre 35 cm y 75 cm)
                dist_dinamica = int(550 + 200 * math.sin(t * 1.5))
                distancia_mm = dist_dinamica
                estado = 0


            med = Medicion(
                angulo=angulo,
                distancia_mm=distancia_mm,
                estado=estado,
                timestamp=t
            )

            if self._cola.full():
                try:
                    self._cola.get_nowait()
                except queue.Empty:
                    pass
            self._cola.put_nowait(med)

            # Avanzar ángulo
            angulo += direccion * self.paso_grados
            if angulo >= 180:
                angulo = 180
                direccion = -1
            elif angulo <= 0:
                angulo = 0
                direccion = 1

            time.sleep(self.periodo_paso_s)

    def obtener_mediciones(self) -> List[Medicion]:
        mediciones = []
        while not self._cola.empty():
            try:
                mediciones.append(self._cola.get_nowait())
            except queue.Empty:
                break
        return mediciones

    def enviar_comando(self, comando: str) -> bool:
        print(f"[Simulador] Comando recibido: {comando.strip()}")
        return True
