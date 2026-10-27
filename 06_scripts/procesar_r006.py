"""Extrae y valida el tramo del Sendero al Ilaló usado en el piloto."""

from pathlib import Path
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from shapely.geometry import LineString


ID_VIA = "198954451"
NODO_INICIO = "12867182981"
NODO_CIMA = "12867182975"
FECHA = "2026-10-05"


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontro la carpeta principal del proyecto")


proyecto = localizar_proyecto()
archivo_original = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / f"R006_ilalo_osm_{FECHA}.osm"
)
archivo_intermedio = (
    proyecto
    / "03_datos_intermedios"
    / "trazados"
    / f"R006_trazado_ida_continuo_{FECHA}.geojson"
)

raiz = ET.parse(archivo_original).getroot()
nodos = {
    elemento.attrib["id"]: (
        float(elemento.attrib["lon"]),
        float(elemento.attrib["lat"]),
    )
    for elemento in raiz.findall("node")
}

via = next(
    elemento
    for elemento in raiz.findall("way")
    if elemento.attrib["id"] == ID_VIA
)
referencias = [nodo.attrib["ref"] for nodo in via.findall("nd")]

indice_inicio = referencias.index(NODO_INICIO)
indice_cima = referencias.index(NODO_CIMA)
paso = 1 if indice_inicio <= indice_cima else -1
referencias_tramo = referencias[indice_inicio : indice_cima + paso : paso]
coordenadas = [nodos[referencia] for referencia in referencias_tramo]
geometria = LineString(coordenadas)

resultado = gpd.GeoDataFrame(
    [
        {
            "id_ruta": "R006",
            "nombre": "Sendero al Ilaló",
            "id_via_osm": ID_VIA,
            "nodo_inicio": NODO_INICIO,
            "nodo_fin": NODO_CIMA,
            "estado": "continuo",
            "fecha": FECHA,
            "geometry": geometria,
        }
    ],
    crs="EPSG:4326",
)

distancia_km = float(resultado.to_crs(32717).length.iloc[0] / 1000)
resultado["distancia_km"] = round(distancia_km, 3)
resultado.to_file(archivo_intermedio, driver="GeoJSON")

comprobacion = gpd.read_file(archivo_intermedio)

print("Archivo original:", archivo_original.name)
print("Nodos del extracto:", len(raiz.findall("node")))
print("Vias del extracto:", len(raiz.findall("way")))
print("Via utilizada:", ID_VIA)
print("Nodos del tramo:", len(referencias_tramo))
print("Geometria resultante:", comprobacion.geometry.iloc[0].geom_type)
print("Geometria valida:", comprobacion.geometry.iloc[0].is_valid)
print("Distancia de ida:", round(distancia_km, 3), "km")
print("Distancia preliminar de ida y vuelta:", round(distancia_km * 2, 3), "km")

assert archivo_original.exists()
assert NODO_INICIO in referencias
assert NODO_CIMA in referencias
assert len(referencias_tramo) >= 2
assert comprobacion.crs.to_epsg() == 4326
assert comprobacion.geometry.iloc[0].geom_type == "LineString"
assert comprobacion.geometry.iloc[0].is_valid

print("Trazado intermedio de R006 guardado y validado correctamente")
