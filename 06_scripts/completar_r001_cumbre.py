"""Añade a R001 la vía OSM que conecta el trazado inicial con la cumbre."""

from pathlib import Path
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from shapely.geometry import LineString, Point


ID_VIA = "377339146"
ID_NODO_CUMBRE = "249414034"
ELEVACION_OSM_CUMBRE_M = 4696
FECHA = "2026-10-05"


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


proyecto = localizar_proyecto()
archivo_base = (
    proyecto
    / "03_datos_intermedios"
    / "trazados"
    / "R001_trazado_subida_continuo_2026-10-01.geojson"
)
archivo_complemento = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / "R001_conexion_cumbre_osm_2026-10-05.osm"
)
archivo_salida = (
    proyecto
    / "03_datos_intermedios"
    / "trazados"
    / "R001_trazado_subida_cumbre_2026-10-05.geojson"
)

base = gpd.read_file(archivo_base)
assert len(base) == 1
coordenadas_base = list(base.geometry.iloc[0].coords)

raiz = ET.parse(archivo_complemento).getroot()
nodos = {
    nodo.attrib["id"]: (
        float(nodo.attrib["lon"]),
        float(nodo.attrib["lat"]),
    )
    for nodo in raiz.findall("node")
}
via = next(
    elemento
    for elemento in raiz.findall("way")
    if elemento.attrib["id"] == ID_VIA
)
referencias = [nodo.attrib["ref"] for nodo in via.findall("nd")]
coordenadas_complemento = [nodos[ref] for ref in referencias]

extremo_base = Point(coordenadas_base[-1])
if Point(coordenadas_complemento[-1]).distance(extremo_base) < Point(
    coordenadas_complemento[0]
).distance(extremo_base):
    coordenadas_complemento.reverse()

separacion_union = extremo_base.distance(Point(coordenadas_complemento[0]))
assert separacion_union < 1e-10
assert coordenadas_complemento[-1] == nodos[ID_NODO_CUMBRE]

geometria_completa = LineString(
    coordenadas_base + coordenadas_complemento[1:]
)
resultado = gpd.GeoDataFrame(
    [
        {
            "id_ruta": "R001",
            "tramo": "subida",
            "origen": "Cruz Loma",
            "destino": "Cumbre Rucu Pichincha",
            "via_complementaria": ID_VIA,
            "nodo_cumbre": ID_NODO_CUMBRE,
            "elevacion_osm_cumbre_m": ELEVACION_OSM_CUMBRE_M,
            "fecha_revision": FECHA,
            "geometry": geometria_completa,
        }
    ],
    crs="EPSG:4326",
)
distancia_km = float(resultado.to_crs(32717).length.iloc[0] / 1000)
resultado["distancia_km"] = round(distancia_km, 3)
resultado.to_file(archivo_salida, driver="GeoJSON")

comprobacion = gpd.read_file(archivo_salida)
print("Vía complementaria:", ID_VIA)
print("Nodos del complemento:", len(referencias))
print("Nodo de cumbre:", ID_NODO_CUMBRE)
print("Elevación etiquetada en OSM:", ELEVACION_OSM_CUMBRE_M, "m")
print("Geometría resultante:", geometria_completa.geom_type)
print("Geometría válida:", geometria_completa.is_valid)
print("Distancia corregida de subida:", round(distancia_km, 3), "km")
print("Distancia preliminar de ida y vuelta:", round(distancia_km * 2, 3), "km")
print("Archivo guardado:", archivo_salida.name)

assert comprobacion.crs.to_epsg() == 4326
assert comprobacion.geometry.iloc[0].geom_type == "LineString"
assert comprobacion.geometry.iloc[0].is_valid
assert distancia_km > float(base.loc[0, "distancia_km"])

print("Conexión de R001 con la cumbre validada correctamente")
