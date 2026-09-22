#!/usr/bin/env python3
"""
radar_model.py

Modelo de datos y estado del radar de ultrasonido.
Mantiene el barrido angular de 0° a 180°, gestiona el desvanecimiento (persistencia fósforo)
y calcula posiciones cartesianas para su renderizado en pantalla.
"""

import time
import math
from typing import Dict, List, Optional
from dataclasses import dataclass
from lector_serie import Medicion


@dataclass
class PuntoEco:
    angulo: int
    distancia_mm: int
    estado: int
    timestamp: float
    direccion: int = 1   # +1 si el barrido iba hacia 180°, -1 si iba hacia 0°

    @property
    def distancia_cm(self) -> float:
        return self.distancia_mm / 10.0

    @property
    def es_valida(self) -> bool:
        return self.estado == 0 and self.distancia_mm > 0

    def intensidad(self, tiempo_actual: float, duracion_persistencia_s: float = 3.5) -> float:
        """Calcula la opacidad / intensidad residual (1.0 = nuevo, 0.0 = desvanecido)."""
        dt = tiempo_actual - self.timestamp
        if dt < 0:
            return 1.0
        if dt >= duracion_persistencia_s:
            return 0.0
        factor = 1.0 - (dt / duracion_persistencia_s)
        return max(0.0, factor ** 1.2)



class RadarModel:
    def __init__(
        self,
        rango_max_mm: int = 1000,
        rango_min_mm: int = 40,
        persistencia_segundos: float = 8.5
    ):

        self.rango_max_mm = rango_max_mm
        self.rango_min_mm = rango_min_mm
        self.persistencia_segundos = persistencia_segundos

        # Almacén de los últimos ecos por ángulo (0 a 180)
        self.ecos: Dict[int, PuntoEco] = {}
        self.angulo_actual: int = 90
        self.ultima_distancia_mm: int = 0
        self.ultimo_estado: int = 0
        self.direccion_barrido: int = 1  # +1 aumentando ángulo, -1 disminuyendo
        self.total_mediciones_recibidas: int = 0

    def actualizar_medicion(self, m: Medicion):
        """Procesa una nueva medición proveniente del lector serie."""
        angulo_clamped = max(0, min(180, m.angulo))

        # Determinar dirección de barrido
        if angulo_clamped > self.angulo_actual:
            self.direccion_barrido = 1
        elif angulo_clamped < self.angulo_actual:
            self.direccion_barrido = -1

        self.angulo_actual = angulo_clamped
        self.ultima_distancia_mm = m.distancia_mm
        self.ultimo_estado = m.estado
        self.total_mediciones_recibidas += 1

        # Guardar o actualizar eco en este ángulo con dirección del barrido
        self.ecos[angulo_clamped] = PuntoEco(
            angulo=angulo_clamped,
            distancia_mm=m.distancia_mm,
            estado=m.estado,
            timestamp=m.timestamp,
            direccion=self.direccion_barrido
        )


    def limpiar(self):
        """Reinicia todos los ecos almacenados."""
        self.ecos.clear()

    def obtener_ecos_suavizados(self, tiempo_actual: Optional[float] = None, ventana: int = 3) -> List[PuntoEco]:
        """
        Devuelve los ecos activos con la distancia suavizada mediante una media móvil ponderada
        sobre los `ventana` vecinos angulares a cada lado. Útil para reducir el 'serrado' causado
        por las reflexiones oblicuas del sensor HC-SR04 en superficies planas.
        Los datos originales en self.ecos NO se modifican.
        """
        if tiempo_actual is None:
            tiempo_actual = time.time()

        activos = self.obtener_ecos_activos(tiempo_actual)
        if not activos:
            return []

        # Índice rápido de distancias crudas por ángulo
        dist_por_angulo: Dict[int, int] = {
            eco.angulo: eco.distancia_mm
            for eco in self.ecos.values()
            if eco.es_valida and self.rango_min_mm <= eco.distancia_mm <= self.rango_max_mm
        }

        resultado = []
        for eco in activos:
            # Recolectar vecinos dentro de la ventana angular
            pesos_total = 0.0
            suma_ponderada = 0.0
            for delta in range(-ventana, ventana + 1):
                ang_vecino = eco.angulo + delta
                if ang_vecino in dist_por_angulo:
                    # Peso triangular: mayor en el centro, decrece linealmente
                    peso = ventana + 1 - abs(delta)
                    suma_ponderada += dist_por_angulo[ang_vecino] * peso
                    pesos_total += peso

            dist_suavizada = int(suma_ponderada / pesos_total) if pesos_total > 0 else eco.distancia_mm

            # Crear copia del eco con la distancia suavizada
            resultado.append(PuntoEco(
                angulo=eco.angulo,
                distancia_mm=dist_suavizada,
                estado=eco.estado,
                timestamp=eco.timestamp,
                direccion=eco.direccion
            ))

        return resultado

    def obtener_ecos_activos(self, tiempo_actual: Optional[float] = None) -> List[PuntoEco]:
        """Devuelve los ecos válidos dentro del rango observable que aún no se hayan desvanecido."""
        if tiempo_actual is None:
            tiempo_actual = time.time()

        activos = []
        for eco in self.ecos.values():
            if (
                eco.es_valida
                and self.rango_min_mm <= eco.distancia_mm <= self.rango_max_mm
                and eco.intensidad(tiempo_actual, self.persistencia_segundos) > 0.01
            ):
                activos.append(eco)
        return activos


    def calcular_coordenadas_xy(
        self,
        angulo_grados: int,
        distancia_mm: int,
        centro_x: int,
        centro_y: int,
        radio_px: int
    ) -> tuple[int, int]:
        """
        Convierte coordenadas polares (ángulo, distancia) a píxeles de pantalla (X, Y).
        0° apunta hacia la derecha (+X), 90° hacia arriba (-Y), 180° hacia la izquierda (-X).
        """
        fraccion_radio = distancia_mm / float(self.rango_max_mm)
        r = fraccion_radio * radio_px

        rad = math.radians(angulo_grados)
        # En pantalla Y crece hacia abajo:
        x = int(centro_x + r * math.cos(rad))
        y = int(centro_y - r * math.sin(rad))
        return x, y

