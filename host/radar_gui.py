#!/usr/bin/env python3
"""
radar_gui.py

Interfaz gráfica de alta fidelidad para el Radar de Ultrasonido (InDEA - UTN FRM).
Implementa una pantalla PPI (Plan Position Indicator) con estética fósforo verde militar/laboratorio,
cuadrículas polares, estela de barrido translúcida y panel lateral de telemetría en tiempo real.
"""

import sys
import math
import time
import pygame
from typing import Optional
from lector_serie import LectorSerie
from radar_model import RadarModel, PuntoEco


# --- Paleta de Colores HUD / Fósforo Verde ---
COLOR_BG = (8, 14, 12)            # Fondo casi negro con tinte verdoso
COLOR_PANEL_BG = (12, 22, 18)      # Fondo paneles laterales
COLOR_PANEL_BORDER = (28, 64, 48)  # Bordes de paneles
COLOR_GRID_DARK = (16, 44, 30)     # Líneas secundarias de la grilla
COLOR_GRID_MAIN = (32, 100, 68)    # Círculos y ejes principales
COLOR_GRID_TEXT = (90, 190, 140)   # Texto de etiquetas y grados
COLOR_BEAM = (140, 255, 190)       # Haz luminoso principal
COLOR_BEAM_TRAIL = (40, 220, 120)  # Estela de desvanecimiento
COLOR_ECHO_BRIGHT = (255, 70, 70)  # Eco / obstáculo detectado (rojo brillante con resplandor)
COLOR_ECHO_GLOW = (255, 140, 40)   # Resplandor naranja de obstáculo
COLOR_TEXT_VALUE = (160, 255, 200) # Valores numéricos destacados
COLOR_TEXT_DIM = (100, 140, 120)   # Texto secundario
COLOR_STATUS_OK = (60, 240, 120)   # Estado conectado
COLOR_STATUS_WARN = (255, 180, 50) # Estado reconectando / advertencia
COLOR_STATUS_ERR = (255, 70, 70)   # Estado error / desconectado


class RadarGUI:
    def __init__(
        self,
        lector: LectorSerie,
        modelo: Optional[RadarModel] = None,
        ancho: int = 1100,
        alto: int = 700
    ):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("InDEA - Radar de Ultrasonido PPI")

        self.ancho = ancho
        self.alto = alto
        self.pantalla = pygame.display.set_mode((self.ancho, self.alto), pygame.RESIZABLE)
        self.reloj = pygame.time.Clock()

        self.lector = lector
        self.modelo = modelo or RadarModel(rango_max_mm=1000)

        # Superficies auxiliares para transparencias (Alfa)
        self.sup_barrido = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        self.sup_ecos = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)

        # Fuentes tipográficas
        self.fuente_grande = pygame.font.SysFont("monospace", 28, bold=True)
        self.fuente_media = pygame.font.SysFont("monospace", 18, bold=True)
        self.fuente_chica = pygame.font.SysFont("monospace", 13)
        self.fuente_micro = pygame.font.SysFont("monospace", 11)

        self.pausado = False
        self.ejecutando = True

    def ejecutar(self):
        """Bucle principal de la interfaz gráfica."""
        self.lector.iniciar()

        while self.ejecutando:
            self._manejar_eventos()

            if not self.pausado:
                # Adquirir nuevas mediciones del puerto serie
                nuevas_mediciones = self.lector.obtener_mediciones()
                for m in nuevas_mediciones:
                    self.modelo.actualizar_medicion(m)

            self._dibujar()
            self.reloj.tick(60) # 60 FPS estables

        self.lector.detener()
        pygame.quit()

    def _manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.ejecutando = False

            elif evento.type == pygame.VIDEORESIZE:
                self.ancho = max(800, evento.w)
                self.alto = max(550, evento.h)
                self.pantalla = pygame.display.set_mode((self.ancho, self.alto), pygame.RESIZABLE)
                self.sup_barrido = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
                self.sup_ecos = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE or evento.key == pygame.K_q:
                    self.ejecutando = False
                elif evento.key == pygame.K_SPACE:
                    self.pausado = not self.pausado
                elif evento.key == pygame.K_r:
                    self.modelo.limpiar()
                elif evento.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_UP):
                    # Aumentar rango máximo en pasos de 250 mm
                    if self.modelo.rango_max_mm < 4000:
                        self.modelo.rango_max_mm += 250
                elif evento.key in (pygame.K_MINUS, pygame.K_KP_MINUS, pygame.K_DOWN):
                    # Disminuir rango máximo en pasos de 250 mm
                    if self.modelo.rango_max_mm > 250:
                        self.modelo.rango_max_mm -= 250

    def _dibujar(self):
        self.pantalla.fill(COLOR_BG)

        # Geometría del radar
        ancho_radar = int(self.ancho * 0.72)
        centro_x = ancho_radar // 2
        centro_y = self.alto - 60
        radio_radar = min(centro_x - 40, centro_y - 60)

        # 1. Dibujar Grilla Polar (Arcos concéntricos y radios angulares)
        self._dibujar_grilla_polar(centro_x, centro_y, radio_radar)

        # 2. Dibujar Ecos / Obstáculos detectados con desvanecimiento de fósforo
        self._dibujar_ecos(centro_x, centro_y, radio_radar)

        # 3. Dibujar Haz y Estela de Barrido
        self._dibujar_haz_barrido(centro_x, centro_y, radio_radar)

        # 4. Dibujar Panel Lateral de Telemetría e Información
        self._dibujar_panel_telemetria(ancho_radar)

        pygame.display.flip()

    def _dibujar_grilla_polar(self, cx: int, cy: int, radio: int):
        # Fondo del domo semicircular
        pygame.draw.circle(self.pantalla, (10, 20, 16), (cx, cy), radio)

        # Arcos concéntricos de distancia (anillos de rango)
        num_anillos = 4
        for i in range(1, num_anillos + 1):
            r_anillo = int((radio / num_anillos) * i)
            dist_marcada_mm = int((self.modelo.rango_max_mm / num_anillos) * i)
            rect = pygame.Rect(cx - r_anillo, cy - r_anillo, r_anillo * 2, r_anillo * 2)

            color_linea = COLOR_GRID_MAIN if i == num_anillos else COLOR_GRID_DARK
            grosor = 2 if i == num_anillos else 1
            pygame.draw.arc(self.pantalla, color_linea, rect, 0, math.pi, grosor)

            # Etiqueta de distancia legible en cm / m
            if self.modelo.rango_max_mm <= 1500:
                txt_dist = f"{dist_marcada_mm // 10} cm"
            else:
                txt_dist = f"{dist_marcada_mm / 1000.0:.2f} m"

            surf_dist = self.fuente_micro.render(txt_dist, True, COLOR_GRID_TEXT)
            self.pantalla.blit(surf_dist, (cx + 5, cy - r_anillo + 4))

        # Línea de base (eje 0° - 180°)
        pygame.draw.line(self.pantalla, COLOR_GRID_MAIN, (cx - radio, cy), (cx + radio, cy), 2)

        # Rayos angulares cada 15° o 30°
        angulos = [0, 30, 45, 60, 90, 120, 135, 150, 180]
        for ang in angulos:
            rad = math.radians(ang)
            x_fin = int(cx + radio * math.cos(rad))
            y_fin = int(cy - radio * math.sin(rad))

            color_rayo = COLOR_GRID_MAIN if ang in (0, 90, 180) else COLOR_GRID_DARK
            pygame.draw.line(self.pantalla, color_rayo, (cx, cy), (x_fin, y_fin), 1)

            # Etiquetas angulares en el perímetro exterior
            x_txt = int(cx + (radio + 22) * math.cos(rad))
            y_txt = int(cy - (radio + 22) * math.sin(rad))
            txt_ang = f"{ang}°"
            surf_ang = self.fuente_chica.render(txt_ang, True, COLOR_GRID_TEXT)
            rect_txt = surf_ang.get_rect(center=(x_txt, y_txt))
            self.pantalla.blit(surf_ang, rect_txt)

    def _dibujar_ecos(self, cx: int, cy: int, radio: int):
        self.sup_ecos.fill((0, 0, 0, 0))
        t_ahora = time.time()
        ecos_activos = self.modelo.obtener_ecos_activos(t_ahora)

        for eco in ecos_activos:
            if not eco.es_valida:
                continue

            intensidad = eco.intensidad(t_ahora, self.modelo.persistencia_segundos)
            x, y = self.modelo.calcular_coordenadas_xy(
                eco.angulo, eco.distancia_mm, cx, cy, radio
            )

            # Efecto de halo brillante con transparencia
            alfa_glow = int(140 * intensidad)
            alfa_core = int(255 * intensidad)

            # Resplandor exterior
            pygame.draw.circle(self.sup_ecos, (*COLOR_ECHO_GLOW, alfa_glow), (x, y), 8)
            # Núcleo del obstáculo
            pygame.draw.circle(self.sup_ecos, (*COLOR_ECHO_BRIGHT, alfa_core), (x, y), 4)

        self.pantalla.blit(self.sup_ecos, (0, 0))

    def _dibujar_haz_barrido(self, cx: int, cy: int, radio: int):
        self.sup_barrido.fill((0, 0, 0, 0))
        ang_actual = self.modelo.angulo_actual
        direccion = self.modelo.direccion_barrido

        # Estela translúcida detrás del haz (persistencia angular)
        ancho_estela = 14  # grados de estela
        for offset in range(ancho_estela):
            ang_estela = ang_actual - (offset * direccion)
            if 0 <= ang_estela <= 180:
                rad_estela = math.radians(ang_estela)
                x_dest = int(cx + radio * math.cos(rad_estela))
                y_dest = int(cy - radio * math.sin(rad_estela))

                # Opacidad decreciente
                alfa = int(60 * (1.0 - (offset / ancho_estela)))
                pygame.draw.line(
                    self.sup_barrido,
                    (*COLOR_BEAM_TRAIL, alfa),
                    (cx, cy),
                    (x_dest, y_dest),
                    3
                )

        # Haz principal luminoso
        rad_haz = math.radians(ang_actual)
        x_haz = int(cx + radio * math.cos(rad_haz))
        y_haz = int(cy - radio * math.sin(rad_haz))
        pygame.draw.line(self.sup_barrido, COLOR_BEAM, (cx, cy), (x_haz, y_haz), 2)

        # Punto central pivote
        pygame.draw.circle(self.pantalla, COLOR_BEAM, (cx, cy), 6)

        self.pantalla.blit(self.sup_barrido, (0, 0))

    def _dibujar_panel_telemetria(self, x_panel: int):
        ancho_panel = self.ancho - x_panel - 20
        rect_panel = pygame.Rect(x_panel, 20, ancho_panel, self.alto - 40)

        # Marco del panel
        pygame.draw.rect(self.pantalla, COLOR_PANEL_BG, rect_panel, border_radius=8)
        pygame.draw.rect(self.pantalla, COLOR_PANEL_BORDER, rect_panel, 2, border_radius=8)

        y_cursor = 35
        margen_x = x_panel + 16

        # Título
        titulo = self.fuente_media.render("RADAR TELEMETRÍA", True, COLOR_BEAM)
        self.pantalla.blit(titulo, (margen_x, y_cursor))
        y_cursor += 35

        # Estado del enlace serie
        if self.lector.conectado:
            txt_estado = "CONECTADO"
            color_est = COLOR_STATUS_OK
        else:
            txt_estado = "REINTENTANDO..." if self.lector._ejecutando else "DESCONECTADO"
            color_est = COLOR_STATUS_WARN if self.lector._ejecutando else COLOR_STATUS_ERR

        puerto_txt = self.lector.puerto_configurado or "Auto-detect"
        self.pantalla.blit(self.fuente_chica.render("PUERTO SERIE:", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        self.pantalla.blit(self.fuente_chica.render(f"{puerto_txt}", True, COLOR_TEXT_VALUE), (margen_x + 110, y_cursor))
        y_cursor += 20

        self.pantalla.blit(self.fuente_chica.render("ESTADO:", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        self.pantalla.blit(self.fuente_chica.render(f"{txt_estado}", True, color_est), (margen_x + 110, y_cursor))
        y_cursor += 30

        pygame.draw.line(self.pantalla, COLOR_PANEL_BORDER, (margen_x, y_cursor), (x_panel + ancho_panel - 16, y_cursor))
        y_cursor += 15

        # Medición Actual - Ángulo
        self.pantalla.blit(self.fuente_chica.render("ÁNGULO SERVO:", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 18
        txt_ang_val = f"{self.modelo.angulo_actual:3d}°"
        self.pantalla.blit(self.fuente_grande.render(txt_ang_val, True, COLOR_BEAM), (margen_x, y_cursor))
        y_cursor += 40

        # Medición Actual - Distancia
        self.pantalla.blit(self.fuente_chica.render("DISTANCIA ECO:", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 18

        if self.modelo.ultimo_estado == 0 and self.modelo.ultima_distancia_mm > 0:
            dist_cm = self.modelo.ultima_distancia_mm / 10.0
            txt_dist_val = f"{dist_cm:5.1f} cm"
            color_dist = COLOR_TEXT_VALUE
        elif self.modelo.ultimo_estado == 1:
            txt_dist_val = "SIN ECO"
            color_dist = COLOR_STATUS_WARN
        else:
            txt_dist_val = "FILTRADO"
            color_dist = COLOR_STATUS_ERR

        self.pantalla.blit(self.fuente_grande.render(txt_dist_val, True, color_dist), (margen_x, y_cursor))
        y_cursor += 45

        # Barra visual de distancia
        ancho_barra = ancho_panel - 32
        alto_barra = 12
        pygame.draw.rect(self.pantalla, COLOR_GRID_DARK, (margen_x, y_cursor, ancho_barra, alto_barra), border_radius=3)
        if self.modelo.ultimo_estado == 0 and self.modelo.ultima_distancia_mm > 0:
            pct = min(1.0, self.modelo.ultima_distancia_mm / float(self.modelo.rango_max_mm))
            w_progreso = int(ancho_barra * pct)
            pygame.draw.rect(self.pantalla, COLOR_ECHO_GLOW, (margen_x, y_cursor, w_progreso, alto_barra), border_radius=3)
        y_cursor += 30

        pygame.draw.line(self.pantalla, COLOR_PANEL_BORDER, (margen_x, y_cursor), (x_panel + ancho_panel - 16, y_cursor))
        y_cursor += 15

        # Parámetros del sistema
        self.pantalla.blit(self.fuente_chica.render(f"RANGO MÁX: {self.modelo.rango_max_mm / 1000.0:.1f} m", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 20
        self.pantalla.blit(self.fuente_chica.render(f"TOTAL MEDS: {self.modelo.total_mediciones_recibidas}", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 35

        # Controles y atajos de teclado
        pygame.draw.line(self.pantalla, COLOR_PANEL_BORDER, (margen_x, y_cursor), (x_panel + ancho_panel - 16, y_cursor))
        y_cursor += 15
        self.pantalla.blit(self.fuente_chica.render("ATAJOS DE TECLADO:", True, COLOR_GRID_TEXT), (margen_x, y_cursor))
        y_cursor += 22
        self.pantalla.blit(self.fuente_micro.render("[ESPACIO] Pausar / Reanudar", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 18
        self.pantalla.blit(self.fuente_micro.render("[R]       Limpiar ecos", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 18
        self.pantalla.blit(self.fuente_micro.render("[+/-]     Ajustar rango máx", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 18
        self.pantalla.blit(self.fuente_micro.render("[ESC / Q] Salir", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
