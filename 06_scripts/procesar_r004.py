"""Construye y valida el trazado circular de R004, Circuito Pondoña."""

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


ID_VIA_CONECTOR = "1057987723"
ID_VIA_CIRCUITO = "1057987724"
NODO_INICIO = "9721343634"
NODO_UNION = "9721343648"
NODO_SENAL = "10025787156"
FECHA = "2026-10-06"


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def leer_via(archivo: Path, id_via: str):
    raiz = ET.parse(archivo).getroot()
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
        if elemento.attrib["id"] == id_via
    )
    referencias = [elemento.attrib["ref"] for elemento in via.findall("nd")]
    etiquetas = {
        elemento.attrib["k"]: elemento.attrib["v"]
        for elemento in via.findall("tag")
    }
    return nodos, referencias, etiquetas


def distancia_haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
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
archivo_conector = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / f"R004_pondona_conector_osm_{FECHA}.osm"
)
archivo_circuito = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / f"R004_pondona_circuito_osm_{FECHA}.osm"
)
archivo_senal = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / f"R004_pondona_senal_osm_{FECHA}.osm"
)
archivo_intermedio = (
    proyecto
    / "03_datos_intermedios"
    / "trazados"
    / f"R004_trazado_circular_continuo_{FECHA}.geojson"
)

nodos_conector, referencias_conector, etiquetas_conector = leer_via(
    archivo_conector, ID_VIA_CONECTOR
)
nodos_circuito, referencias_circuito, etiquetas_circuito = leer_via(
    archivo_circuito, ID_VIA_CIRCUITO
)

compartidos = set(referencias_conector) & set(referencias_circuito)
assert compartidos == {NODO_INICIO, NODO_UNION}
assert referencias_circuito[0] == NODO_UNION
assert referencias_circuito[-1] == NODO_INICIO
assert etiquetas_conector.get("highway") == "path"
assert etiquetas_circuito.get("highway") == "path"

indice_inicio = referencias_conector.index(NODO_INICIO)
indice_union = referencias_conector.index(NODO_UNION)
assert indice_inicio < indice_union

# Solo se utiliza la sección del conector comprendida entre los dos nodos
# compartidos. El ramal anterior conduce al circuito, pero no integra el lazo.
referencias_arco = referencias_conector[indice_inicio : indice_union + 1]
referencias_unidas = referencias_arco + referencias_circuito[1:]
nodos = {**nodos_conector, **nodos_circuito}
coordenadas = [nodos[referencia] for referencia in referencias_unidas]
geometria = LineString(coordenadas)

raiz_senal = ET.parse(archivo_senal).getroot()
senal = next(
    elemento
    for elemento in raiz_senal.findall("node")
    if elemento.attrib["id"] == NODO_SENAL
)
coordenada_senal = (
    float(senal.attrib["lon"]),
    float(senal.attrib["lat"]),
)
separacion_senal_m = distancia_haversine_m(
    coordenada_senal, nodos[NODO_INICIO]
)

resultado = gpd.GeoDataFrame(
    [
        {
            "id_ruta": "R004",
            "nombre": "Circuito Pondoña",
            "vias_osm": f"{ID_VIA_CONECTOR}|{ID_VIA_CIRCUITO}",
            "nodo_inicio": NODO_INICIO,
            "nodo_union": NODO_UNION,
            "nodo_senal": NODO_SENAL,
            "separacion_senal_m": round(separacion_senal_m, 3),
            "tipo_recorrido": "circular",
            "estado": "continuo_cerrado",
            "fecha": FECHA,
            "geometry": geometria,
        }
    ],
    crs="EPSG:4326",
)

distancia_km = float(resultado.to_crs(32617).length.iloc[0] / 1000)
resultado["distancia_total_km"] = round(distancia_km, 3)
resultado.to_file(archivo_intermedio, driver="GeoJSON")

comprobacion = gpd.read_file(archivo_intermedio)

print("Archivos originales:", archivo_conector.name, "|", archivo_circuito.name)
print("Vías utilizadas:", ID_VIA_CONECTOR, "|", ID_VIA_CIRCUITO)
print("Nodos del arco conector:", len(referencias_arco))
print("Nodos de la vía principal:", len(referencias_circuito))
print("Nodos de la cadena cerrada:", len(referencias_unidas))
print("Separación del inicio al letrero:", round(separacion_senal_m, 3), "m")
print("Geometría resultante:", comprobacion.geometry.iloc[0].geom_type)
print("Geometría válida:", comprobacion.geometry.iloc[0].is_valid)
print("Geometría simple:", comprobacion.geometry.iloc[0].is_simple)
print("Circuito cerrado:", coordenadas[0] == coordenadas[-1])
print("Distancia total:", round(distancia_km, 3), "km")

assert archivo_conector.exists()
assert archivo_circuito.exists()
assert archivo_senal.exists()
assert coordenadas[0] == coordenadas[-1]
assert len(referencias_unidas[:-1]) == len(set(referencias_unidas[:-1]))
assert len(comprobacion) == 1
assert comprobacion.crs.to_epsg() == 4326
assert comprobacion.geometry.iloc[0].geom_type == "LineString"
assert comprobacion.geometry.iloc[0].is_valid
assert comprobacion.geometry.iloc[0].is_simple
assert separacion_senal_m < 20

print("Trazado intermedio circular de R004 guardado y validado correctamente")
