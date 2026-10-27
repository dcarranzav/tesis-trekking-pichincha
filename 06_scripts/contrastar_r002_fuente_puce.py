"""Contrasta el trazado R002 con dos observaciones publicadas de Los Pantzas.

La fuente registra coordenadas al segundo de arco, por lo que las distancias
calculadas no prueban identidad centimétrica ni delimitan el sendero completo.
No modifica datos originales ni la decisión de elegibilidad.
"""

from pathlib import Path
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from shapely.geometry import Point


FUENTE = (
    "https://repositorio.puce.edu.ec/server/api/core/bitstreams/"
    "da7154a6-9c6b-4a19-9a42-f49b3fbb2a1e/content"
)
OBSERVACIONES = {
    "Los Pantzas, 03/05/2014, S 0 26 19 / O 78 29 54":
        (-26 / 60 - 19 / 3600, -78 - 29 / 60 - 54 / 3600),
    "Los Pantzas, 31/05/2014, S 0 27 15 / O 78 28 58":
        (-27 / 60 - 15 / 3600, -78 - 28 / 60 - 58 / 3600),
}

proyecto = Path(__file__).resolve().parent.parent
archivo = proyecto / "03_datos_intermedios/trazados/R002_trazado_ida_continuo_2026-10-06.geojson"
trazado = gpd.read_file(archivo).to_crs(32717)
assert len(trazado) == 1
linea = trazado.geometry.iloc[0]
assert linea.geom_type == "LineString" and linea.is_valid

print("Fuente PUCE:", FUENTE)
print("Anexo 10, tabla de residuos del Sendero Los Pantzas, p. 128 del PDF")
print("Longitud de R002 (ida):", round(linea.length / 1000, 3), "km")
for etiqueta, (latitud, longitud) in OBSERVACIONES.items():
    punto = gpd.GeoSeries([Point(longitud, latitud)], crs=4326).to_crs(32717).iloc[0]
    print(etiqueta)
    print("  Distancia perpendicular al trazado:", round(linea.distance(punto), 1), "m")
    print("  Proyección sobre R002 desde el inicio:", round(linea.project(punto) / 1000, 3), "km")

print("Interpretación: coincidencia parcial; identidad y extremo alto aún por verificar.")
