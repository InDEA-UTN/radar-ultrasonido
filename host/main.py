#!/usr/bin/env python3
"""
main.py

Punto de entrada principal para el software de visualización de radar (InDEA - UTN FRM).

Uso:
  python3 host/main.py                     # Conexión automática por puerto serie
  python3 host/main.py -p /dev/ttyACM0      # Especificar puerto serie
  python3 host/main.py -b 115200           # Especificar baudrate
  python3 host/main.py --simular           # Ejecutar en modo simulación virtual
"""

import sys
import argparse
from lector_serie import LectorSerie, listar_puertos_disponibles
from simulador import LectorSimulado
from radar_model import RadarModel
from radar_gui import RadarGUI


def parse_argumentos():
    parser = argparse.ArgumentParser(
        description="Visualizador PPI para Radar de Ultrasonido (InDEA - UTN FRM)"
    )
    parser.add_argument(
        "-p", "--puerto",
        type=str,
        default=None,
        help="Puerto serie del Arduino (ej: /dev/ttyACM0 o COM3). Si no se especifica, se autodetecta."
    )
    parser.add_argument(
        "-b", "--baudrate",
        type=int,
        default=115200,
        help="Velocidad en baudios del puerto serie (por defecto 115200)."
    )
    parser.add_argument(
        "--rango-max",
        type=int,
        default=1000,
        help="Rango máximo inicial en milímetros (por defecto 1000 mm = 1 m)."
    )
    parser.add_argument(
        "--simular",
        action="store_true",
        help="Ejecuta la interfaz en modo simulación virtual sin hardware."
    )
    return parser.parse_args()


def main():
    args = parse_argumentos()

    print("==================================================")
    print("   RADAR DE ULTRASONIDO - INTERFAZ PPI (InDEA)   ")
    print("==================================================")

    if args.simular:
        print("[Modo] SIMULACIÓN VIRTUAL activada.")
        lector = LectorSimulado()
    else:
        puertos = listar_puertos_disponibles()
        print(f"[Sistema] Puertos serie detectados: {puertos if puertos else 'Ninguno'}")
        if args.puerto:
            print(f"[Conexión] Utilizando puerto especificado: {args.puerto} a {args.baudrate} baudios.")
        else:
            print(f"[Conexión] Modo detección automática a {args.baudrate} baudios.")
        lector = LectorSerie(puerto=args.puerto, baudrate=args.baudrate)

    modelo = RadarModel(rango_max_mm=args.rango_max)
    gui = RadarGUI(lector=lector, modelo=modelo)

    try:
        gui.ejecutar()
    except KeyboardInterrupt:
        print("\n[Sistema] Cierre solicitado por el usuario.")
    finally:
        lector.detener()
        print("[Sistema] Finalizado correctamente.")


if __name__ == "__main__":
    main()
