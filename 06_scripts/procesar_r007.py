"""Construye y valida el trazado sur al volcán El Corazón (R007)."""

from pathlib import Path
import math
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from shapely.geometry import LineString


ID_VIA = "356041538"
NODO_INICIO = "2624530252"
NODO_FIN_OSM = "3674114168"
NODO_CUMBRE = "249409499"
FECHA = "2026-10-06"
UMBRAL_CONEXION_M = 5.0


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def distancia_haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Calcula distancia entre pares (longitud, latitud)."""
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    termino = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * 6_371_008.8 * math.asin(math.sqrt(termino))


proyecto = localizar_proyecto()
archivo_via = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / f"R007_corazon_sur_osm_{FECHA}.osm"
)
archivo_cumbre = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / f"R007_corazon_cumbre_osm_{FECHA}.osm"
)
archivo_intermedio = (
    proyecto
    / "03_datos_intermedios"
    / "trazados"
    / f"R007_trazado_ida_continuo_{FECHA}.geojson"
)

raiz_via = ET.parse(archivo_via).getroot()
nodos = {
    elemento.attrib["id"]: (
        float(elemento.attrib["lon"]),
        float(elemento.attrib["lat"]),
    )
    for elemento in raiz_via.findall("node")
}
via = next(
    elemento
    for elemento in raiz_via.findall("way")
    if elemento.attrib["id"] == ID_VIA
)
referencias = [elemento.attrib["ref"] for elemento in via.findall("nd")]

raiz_cumbre = ET.parse(archivo_cumbre).getroot()
cumbre = next(
    elemento
    for elemento in raiz_cumbre.findall("node")
    if elemento.attrib["id"] == NODO_CUMBRE
)
coordenada_cumbre = (
    float(cumbre.attrib["lon"]),
    float(cumbre.attrib["lat"]),
)

assert referencias[0] == NODO_INICIO
assert referencias[-1] == NODO_FIN_OSM
assert len(referencias) == len(set(referencias))

coordenadas = [nodos[referencia] for referencia in referencias]
separacion_cumbre_m = distancia_haversine_m(
    coordenadas[-1], coordenada_cumbre
)
assert separacion_cumbre_m <= UMBRAL_CONEXION_M

# El extremo cartografiado queda a 2,1 m del nodo de cumbre. Se agrega ese
# único punto para representar el destino declarado y conservar la vía intacta.
coordenadas.append(coordenada_cumbre)
geometria = LineString(coordenadas)

resultado = gpd.GeoDataFrame(
    [
        {
            "id_ruta": "R007",
            "nombre": "Sendero sur al volcán El Corazón",
            "id_via_osm": ID_VIA,
            "nodo_inicio": NODO_INICIO,
            "nodo_fin_osm": NODO_FIN_OSM,
            "nodo_cumbre": NODO_CUMBRE,
            "ajuste_m": round(separacion_cumbre_m, 3),
            "estado": "continuo_con_ajuste_documentado",
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

print("Archivo original de la vía:", archivo_via.name)
print("Archivo original de la cumbre:", archivo_cumbre.name)
print("Vía utilizada:", ID_VIA)
print("Nodos originales de la vía:", len(referencias))
print("Separación final hasta la cumbre:", round(separacion_cumbre_m, 3), "m")
print("Geometría resultante:", comprobacion.geometry.iloc[0].geom_type)
print("Geometría válida:", comprobacion.geometry.iloc[0].is_valid)
print("Geometría simple:", comprobacion.geometry.iloc[0].is_simple)
print("Distancia de ida:", round(distancia_km, 3), "km")
print("Distancia preliminar de ida y vuelta:", round(distancia_km * 2, 3), "km")

assert archivo_via.exists()
assert archivo_cumbre.exists()
assert len(comprobacion) == 1
assert comprobacion.crs.to_epsg() == 4326
assert comprobacion.geometry.iloc[0].geom_type == "LineString"
assert comprobacion.geometry.iloc[0].is_valid
assert comprobacion.geometry.iloc[0].is_simple
assert comprobacion.loc[0, "nodo_cumbre"] == NODO_CUMBRE
assert comprobacion.loc[0, "ajuste_m"] <= UMBRAL_CONEXION_M

print("Trazado intermedio de R007 guardado y validado correctamente")
