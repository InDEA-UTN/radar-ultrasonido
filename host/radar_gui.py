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
COLOR_SHADOW_RED = (235, 45, 45)   # Sombra roja proyectada detrás de los obstáculos
COLOR_SHADOW_RED_EDGE = (245, 80, 80) # Bordes laterales de la sombra roja
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
        self.sup_sombras = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        self.sup_barrido = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        self.sup_ecos = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)

        # Fuentes tipográficas
        self.fuente_grande = pygame.font.SysFont("monospace", 28, bold=True)
        self.fuente_media = pygame.font.SysFont("monospace", 18, bold=True)
        self.fuente_chica = pygame.font.SysFont("monospace", 13)
        self.fuente_micro = pygame.font.SysFont("monospace", 11)

        self.pausado = False
        self.ejecutando = True
        # Modo pico: muestra solo el ángulo de máxima incidencia (mínima distancia) por cluster
        self.modo_pico = False

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
                self.sup_sombras = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
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
                elif evento.key == pygame.K_b:
                    # [B] Iniciar/Finalizar calibración de fondo (background)
                    if not self.modelo.calibrando:
                        self.modelo.iniciar_calibracion()
                        self.modelo.limpiar()
                    else:
                        self.modelo.finalizar_calibracion()
                        self.modelo.limpiar()
                elif evento.key == pygame.K_n:
                    # [N] Borrar calibración de fondo (volver a ver todo)
                    self.modelo.limpiar_calibracion()
                    self.modelo.limpiar()
                elif evento.key == pygame.K_l:
                    # [L] Alternar escala lineal / raíz cuadrada (exagera primer plano)
                    self.modelo.escala_logaritmica = not self.modelo.escala_logaritmica
                elif evento.key == pygame.K_p:
                    # [P] Alternar modo pico: solo muestra el ángulo central real del objeto
                    self.modo_pico = not self.modo_pico

    def _dibujar(self):
        self.pantalla.fill(COLOR_BG)


        # Geometría del radar
        ancho_radar = int(self.ancho * 0.72)
        centro_x = ancho_radar // 2
        centro_y = self.alto - 60
        radio_radar = min(centro_x - 40, centro_y - 60)

        # 1. Dibujar Grilla Polar (Arcos concéntricos y radios angulares)
        self._dibujar_grilla_polar(centro_x, centro_y, radio_radar)

        # 2. Dibujar Sombras Proyectadas detrás de los Obstáculos (Efecto Linterna / Oclusión)
        if not self.modo_pico:
            self._dibujar_sombras(centro_x, centro_y, radio_radar)

        # 3. Dibujar Haz y Estela de Barrido (con bloqueo de rayo al chocar obstáculo)
        self._dibujar_haz_barrido(centro_x, centro_y, radio_radar)

        # 4. Dibujar Ecos / Superficie Frontal Iluminada de Obstáculos
        self._dibujar_ecos(centro_x, centro_y, radio_radar)

        # 5. Dibujar Panel Lateral de Telemetría e Información
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

    def _agrupar_ecos_en_clusters(
        self,
        ecos_activos: list[PuntoEco],
        max_delta_ang: int = 3,
        max_delta_dist_mm: int = 60,
    ) -> list[list[PuntoEco]]:
        """Agrupa ecos válidos contiguos en clústeres según cercanía angular y de distancia."""
        ecos_ordenados = sorted(ecos_activos, key=lambda e: e.angulo)
        clusters: list[list[PuntoEco]] = []
        cluster_actual: list[PuntoEco] = []

        for eco in ecos_ordenados:
            if not eco.es_valida:
                continue
            if not cluster_actual:
                cluster_actual.append(eco)
            elif (
                (eco.angulo - cluster_actual[-1].angulo) <= max_delta_ang
                and abs(eco.distancia_mm - cluster_actual[-1].distancia_mm) <= max_delta_dist_mm
            ):
                cluster_actual.append(eco)
            else:
                clusters.append(cluster_actual)
                cluster_actual = [eco]

        if cluster_actual:
            clusters.append(cluster_actual)
        return clusters

    def _detectar_picos_cluster(
        self,
        cluster: list[PuntoEco],
        ventana_ang: int = 6,
        prominencia_mm: int = 15,
        min_sep_grados: int = 18,
    ) -> list[PuntoEco]:
        """
        Detecta múltiples mínimos locales de distancia dentro de un clúster.
        Permite distinguir varios objetos cuyos arcos ultrasónicos se superpusieron.
        """
        if len(cluster) <= 2:
            return [min(cluster, key=lambda e: e.distancia_mm)]

        ang_ini = cluster[0].angulo
        ang_fin = cluster[-1].angulo
        candidatos: list[PuntoEco] = []

        for eco in cluster:
            # 1. Mínimo local en su vecindad angular
            vecinos = [v for v in cluster if abs(v.angulo - eco.angulo) <= ventana_ang]
            if any(v.distancia_mm < eco.distancia_mm for v in vecinos):
                continue

            # 2. Prominencia: debe haber una subida hacia un valle entre objetos
            izq = [v.distancia_mm for v in cluster if eco.angulo - 15 <= v.angulo < eco.angulo]
            der = [v.distancia_mm for v in cluster if eco.angulo < v.angulo <= eco.angulo + 15]
            sube_izq = bool(izq) and (max(izq) - eco.distancia_mm) >= prominencia_mm
            sube_der = bool(der) and (max(der) - eco.distancia_mm) >= prominencia_mm

            cerca_borde_izq = (eco.angulo - ang_ini) <= ventana_ang
            cerca_borde_der = (ang_fin - eco.angulo) <= ventana_ang

            if (sube_izq and sube_der) or (cerca_borde_izq and sube_der) or (cerca_borde_der and sube_izq):
                candidatos.append(eco)

        # Garantizar al menos el mínimo global del clúster
        min_global = min(cluster, key=lambda e: e.distancia_mm)
        if min_global not in candidatos:
            candidatos.append(min_global)

        # 3. Supresión de no-mínimos: priorizar los más cercanos y exigir separación mínima
        candidatos.sort(key=lambda e: e.distancia_mm)
        seleccionados: list[PuntoEco] = []
        for cand in candidatos:
            if all(abs(cand.angulo - sel.angulo) >= min_sep_grados for sel in seleccionados):
                seleccionados.append(cand)

        return sorted(seleccionados, key=lambda e: e.angulo)

    def _dibujar_sombras(self, cx: int, cy: int, radio: int):
        """Proyecta sombras radiales rojas completamente uniformes y continuas detrás de los obstáculos."""

        self.sup_sombras.fill((0, 0, 0, 0))
        t_ahora = time.time()
        ecos_activos = self.modelo.obtener_ecos_suavizados(t_ahora)
        if not ecos_activos:
            return

        clusters = self._agrupar_ecos_en_clusters(ecos_activos)

        # Dibujar cada sombra como un único polígono sólido uniforme
        for cluster in clusters:
            if not cluster:
                continue

            intensidad_cluster = max(e.intensidad(t_ahora, self.modelo.persistencia_segundos) for e in cluster)
            if intensidad_cluster <= 0.02:
                continue

            alfa_sombra = int(90 * intensidad_cluster)
            alfa_borde = int(160 * intensidad_cluster)

            if len(cluster) == 1:
                eco = cluster[0]
                delta_ang = 0.9
                ang_izq = max(0.0, eco.angulo - delta_ang)
                ang_der = min(180.0, eco.angulo + delta_ang)

                p_f_izq = self.modelo.calcular_coordenadas_xy(ang_izq, eco.distancia_mm, cx, cy, radio)
                p_f_der = self.modelo.calcular_coordenadas_xy(ang_der, eco.distancia_mm, cx, cy, radio)
                p_o_der = self.modelo.calcular_coordenadas_xy(ang_der, self.modelo.rango_max_mm, cx, cy, radio)
                p_o_izq = self.modelo.calcular_coordenadas_xy(ang_izq, self.modelo.rango_max_mm, cx, cy, radio)

                poligono = [p_f_izq, p_f_der, p_o_der, p_o_izq]
                pygame.draw.polygon(self.sup_sombras, (*COLOR_SHADOW_RED, alfa_sombra), poligono)
                pygame.draw.line(self.sup_sombras, (*COLOR_SHADOW_RED_EDGE, alfa_borde), p_f_izq, p_o_izq, 1)
                pygame.draw.line(self.sup_sombras, (*COLOR_SHADOW_RED_EDGE, alfa_borde), p_f_der, p_o_der, 1)
            else:
                ang_ini = max(0.0, cluster[0].angulo - 0.5)
                ang_fin = min(180.0, cluster[-1].angulo + 0.5)

                # 1. Borde frontal que sigue la forma del obstáculo
                puntos_front = [
                    self.modelo.calcular_coordenadas_xy(ang_ini, cluster[0].distancia_mm, cx, cy, radio)
                ]
                for e in cluster:
                    puntos_front.append(self.modelo.calcular_coordenadas_xy(e.angulo, e.distancia_mm, cx, cy, radio))
                puntos_front.append(
                    self.modelo.calcular_coordenadas_xy(ang_fin, cluster[-1].distancia_mm, cx, cy, radio)
                )

                # 2. Arco exterior perimetral de retorno
                puntos_back = [
                    self.modelo.calcular_coordenadas_xy(ang_fin, self.modelo.rango_max_mm, cx, cy, radio)
                ]
                for e in reversed(cluster):
                    puntos_back.append(self.modelo.calcular_coordenadas_xy(e.angulo, self.modelo.rango_max_mm, cx, cy, radio))
                puntos_back.append(
                    self.modelo.calcular_coordenadas_xy(ang_ini, self.modelo.rango_max_mm, cx, cy, radio)
                )

                # 3. Dibujar polígono continuo unificado (sin líneas internas ni solapes de alfa)
                poligono_completo = puntos_front + puntos_back
                pygame.draw.polygon(self.sup_sombras, (*COLOR_SHADOW_RED, alfa_sombra), poligono_completo)

                # 4. Trazar exclusivamente los dos rayos delimitadores externos
                pygame.draw.line(self.sup_sombras, (*COLOR_SHADOW_RED_EDGE, alfa_borde), puntos_front[0], puntos_back[-1], 1)
                pygame.draw.line(self.sup_sombras, (*COLOR_SHADOW_RED_EDGE, alfa_borde), puntos_front[-1], puntos_back[0], 1)

        self.pantalla.blit(self.sup_sombras, (0, 0))

    def _dibujar_ecos(self, cx: int, cy: int, radio: int):
        """Dibuja la zona iluminada (sensor→obstáculo) y la línea frontal del obstáculo."""
        self.sup_ecos.fill((0, 0, 0, 0))
        t_ahora = time.time()
        ecos_activos = self.modelo.obtener_ecos_suavizados(t_ahora)
        if not ecos_activos:
            return

        clusters = self._agrupar_ecos_en_clusters(ecos_activos)

        if self.modo_pico:
            picos_globales: list[tuple[PuntoEco, int, int]] = []
            for cluster in clusters:
                if len(cluster) < 3:
                    continue
                intensidad_cluster = max(e.intensidad(t_ahora, self.modelo.persistencia_segundos) for e in cluster)
                if intensidad_cluster <= 0.02:
                    continue
                alfa_linea = int(255 * intensidad_cluster)
                alfa_relleno = int(55 * intensidad_cluster)
                for eco_pico in self._detectar_picos_cluster(cluster):
                    picos_globales.append((eco_pico, alfa_linea, alfa_relleno))

            # Supresión global entre clústeres cercanos (evita picos duplicados en bordes rotos)
            picos_globales.sort(key=lambda item: item[0].distancia_mm)
            picos_filtrados: list[tuple[PuntoEco, int, int]] = []
            for item in picos_globales:
                if all(abs(item[0].angulo - sel[0].angulo) >= 18 for sel in picos_filtrados):
                    picos_filtrados.append(item)

            r_cruz = 7
            for eco_pico, alfa_linea, alfa_relleno in picos_filtrados:
                p_pico = self.modelo.calcular_coordenadas_xy(eco_pico.angulo, eco_pico.distancia_mm, cx, cy, radio)
                pygame.draw.line(self.sup_ecos, (*COLOR_BEAM_TRAIL, alfa_relleno * 2), (cx, cy), p_pico, 1)

                pygame.draw.line(self.sup_ecos, (*COLOR_ECHO_BRIGHT, alfa_linea),
                                 (p_pico[0] - r_cruz, p_pico[1]), (p_pico[0] + r_cruz, p_pico[1]), 2)
                pygame.draw.line(self.sup_ecos, (*COLOR_ECHO_BRIGHT, alfa_linea),
                                 (p_pico[0], p_pico[1] - r_cruz), (p_pico[0], p_pico[1] + r_cruz), 2)
                pygame.draw.circle(self.sup_ecos, (*COLOR_ECHO_GLOW, int(alfa_linea * 0.7)), p_pico, r_cruz + 4, 2)

                dist_cm = eco_pico.distancia_mm / 10.0
                lbl = self.fuente_micro.render(f"{dist_cm:.1f}cm", True, (*COLOR_ECHO_BRIGHT, alfa_linea))
                self.sup_ecos.blit(lbl, (p_pico[0] + r_cruz + 4, p_pico[1] - 7))

            self.pantalla.blit(self.sup_ecos, (0, 0))
            return

        for cluster in clusters:
            intensidad_cluster = max(e.intensidad(t_ahora, self.modelo.persistencia_segundos) for e in cluster)
            if intensidad_cluster <= 0.02:
                continue

            alfa_linea   = int(255 * intensidad_cluster)
            alfa_relleno = int(55  * intensidad_cluster)

            # === MODO NORMAL: arco completo del cluster ===
            # Relleno zona libre (centro → frente del obstáculo)
            puntos_frente = [
                self.modelo.calcular_coordenadas_xy(e.angulo, e.distancia_mm, cx, cy, radio)
                for e in cluster
            ]
            if len(cluster) >= 2:
                ang_ini = max(0.0,   cluster[0].angulo  - 0.5)
                ang_fin = min(180.0, cluster[-1].angulo + 0.5)
                p_borde_ini = self.modelo.calcular_coordenadas_xy(ang_ini, cluster[0].distancia_mm,  cx, cy, radio)
                p_borde_fin = self.modelo.calcular_coordenadas_xy(ang_fin, cluster[-1].distancia_mm, cx, cy, radio)
                poligono_libre = [(cx, cy), p_borde_ini] + puntos_frente + [p_borde_fin]
            else:
                eco = cluster[0]
                p1 = self.modelo.calcular_coordenadas_xy(max(0.0,   eco.angulo - 1.5), eco.distancia_mm, cx, cy, radio)
                p2 = self.modelo.calcular_coordenadas_xy(min(180.0, eco.angulo + 1.5), eco.distancia_mm, cx, cy, radio)
                poligono_libre = [(cx, cy), p1, p2]

            COLOR_LIBRE = (60, 220, 130)
            pygame.draw.polygon(self.sup_ecos, (*COLOR_LIBRE, alfa_relleno), poligono_libre)

            # Línea frontal del cluster
            if len(cluster) >= 2:
                pygame.draw.lines(self.sup_ecos, (*COLOR_ECHO_BRIGHT, alfa_linea), False, puntos_frente, 3)
            else:
                eco = cluster[0]
                p1 = self.modelo.calcular_coordenadas_xy(max(0.0,   eco.angulo - 1.5), eco.distancia_mm, cx, cy, radio)
                p2 = self.modelo.calcular_coordenadas_xy(min(180.0, eco.angulo + 1.5), eco.distancia_mm, cx, cy, radio)
                pygame.draw.line(self.sup_ecos, (*COLOR_ECHO_BRIGHT, alfa_linea), p1, p2, 3)

        self.pantalla.blit(self.sup_ecos, (0, 0))


    def _dibujar_haz_barrido(self, cx: int, cy: int, radio: int):

        self.sup_barrido.fill((0, 0, 0, 0))
        ang_actual = self.modelo.angulo_actual
        direccion = self.modelo.direccion_barrido

        # Estela translúcida detrás del haz hasta el borde exterior
        ancho_estela = 14  # grados de estela
        for offset in range(ancho_estela):
            ang_estela = ang_actual - (offset * direccion)
            if 0 <= ang_estela <= 180:
                x_dest, y_dest = self.modelo.calcular_coordenadas_xy(
                    ang_estela, self.modelo.rango_max_mm, cx, cy, radio
                )

                # Opacidad decreciente de la luz
                alfa = int(65 * (1.0 - (offset / ancho_estela)))
                pygame.draw.line(
                    self.sup_barrido,
                    (*COLOR_BEAM_TRAIL, alfa),
                    (cx, cy),
                    (x_dest, y_dest),
                    3
                )

        # Haz principal luminoso completo hasta el radio máximo
        rad_haz = math.radians(ang_actual)
        x_haz = int(cx + radio * math.cos(rad_haz))
        y_haz = int(cy - radio * math.sin(rad_haz))
        pygame.draw.line(self.sup_barrido, COLOR_BEAM, (cx, cy), (x_haz, y_haz), 2)

        # Punto central pivote (origen de la linterna / sensor)
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
            if self.modelo.ultima_distancia_mm > self.modelo.rango_max_mm:
                txt_dist_val = f"{dist_cm:4.1f}cm (>MAX)"
                color_dist = COLOR_STATUS_WARN
            elif self.modelo.ultima_distancia_mm < self.modelo.rango_min_mm:
                txt_dist_val = f"{dist_cm:4.1f}cm (<MIN)"
                color_dist = COLOR_STATUS_WARN
            else:
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
        if self.modelo.ultimo_estado == 0 and self.modelo.rango_min_mm <= self.modelo.ultima_distancia_mm <= self.modelo.rango_max_mm:
            pct = self.modelo.ultima_distancia_mm / float(self.modelo.rango_max_mm)
            w_progreso = int(ancho_barra * pct)
            pygame.draw.rect(self.pantalla, COLOR_ECHO_GLOW, (margen_x, y_cursor, w_progreso, alto_barra), border_radius=3)
        elif self.modelo.ultimo_estado == 0 and self.modelo.ultima_distancia_mm > self.modelo.rango_max_mm:
            # Barra completa en color de advertencia por superar el rango máximo configurado
            pygame.draw.rect(self.pantalla, COLOR_STATUS_WARN, (margen_x, y_cursor, ancho_barra, alto_barra), border_radius=3)
        y_cursor += 30


        pygame.draw.line(self.pantalla, COLOR_PANEL_BORDER, (margen_x, y_cursor), (x_panel + ancho_panel - 16, y_cursor))
        y_cursor += 15

        # Parámetros del sistema
        self.pantalla.blit(self.fuente_chica.render(f"RANGO MÁX: {self.modelo.rango_max_mm / 1000.0:.1f} m", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 20
        self.pantalla.blit(self.fuente_chica.render(f"TOTAL MEDS: {self.modelo.total_mediciones_recibidas}", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 20

        # Estado de calibración de fondo
        angulos_cal = len(self.modelo.fondo_mm)
        if self.modelo.calibrando:
            ang_acum = len(self.modelo._cal_acum)
            txt_cal = f"CAL FONDO: {ang_acum}/180°..."
            color_cal = COLOR_STATUS_WARN
        elif angulos_cal > 0:
            txt_cal = f"FONDO: {angulos_cal} pts ✓"
            color_cal = COLOR_STATUS_OK
        else:
            txt_cal = "SIN FONDO CALIB."
            color_cal = COLOR_TEXT_DIM
        self.pantalla.blit(self.fuente_chica.render(txt_cal, True, color_cal), (margen_x, y_cursor))
        y_cursor += 20

        # Margen de fondo activo
        if angulos_cal > 0 or self.modelo.calibrando:
            txt_margen = f"MARGEN FONDO: {self.modelo.margen_fondo_mm} mm"
            self.pantalla.blit(self.fuente_micro.render(txt_margen, True, COLOR_TEXT_DIM), (margen_x, y_cursor))
            y_cursor += 18
        # Escala visual activa
        txt_escala = "ESCALA: √ (1er plano)" if self.modelo.escala_logaritmica else "ESCALA: Lineal"
        color_escala = COLOR_STATUS_WARN if self.modelo.escala_logaritmica else COLOR_TEXT_DIM
        self.pantalla.blit(self.fuente_micro.render(txt_escala, True, color_escala), (margen_x, y_cursor))
        y_cursor += 18
        # Modo pico activo
        txt_pico = "MODO: PICO (ángulo central)" if self.modo_pico else "MODO: Arco completo"
        color_pico = COLOR_ECHO_BRIGHT if self.modo_pico else COLOR_TEXT_DIM
        self.pantalla.blit(self.fuente_micro.render(txt_pico, True, color_pico), (margen_x, y_cursor))
        y_cursor += 5

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
        self.pantalla.blit(self.fuente_micro.render("[B]       Calibrar fondo (vacío→B→B)", True, COLOR_STATUS_WARN), (margen_x, y_cursor))
        y_cursor += 18
        self.pantalla.blit(self.fuente_micro.render("[N]       Borrar calibración fondo", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 18
        self.pantalla.blit(self.fuente_micro.render("[L]       Escala lineal / √ primer plano", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 18
        self.pantalla.blit(self.fuente_micro.render("[P]       Modo pico / arco completo", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
        y_cursor += 18
        self.pantalla.blit(self.fuente_micro.render("[ESC / Q] Salir", True, COLOR_TEXT_DIM), (margen_x, y_cursor))
