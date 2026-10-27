"""Construye y valida el trazado de R002, Sendero Los Pantzas."""

from pathlib import Path
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from shapely.geometry import LineString


ID_VIA_ACCESO = "256471445"
ID_VIA_PRINCIPAL = "205097364"
NODO_INICIO = "2621350520"
NODO_UNION = "2150683165"
NODO_FIN = "9864044574"
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


proyecto = localizar_proyecto()
archivo_acceso = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / f"R002_pantzas_acceso_osm_{FECHA}.osm"
)
archivo_principal = (
    proyecto
    / "02_datos_originales"
    / "trazados"
    / f"R002_pantzas_principal_osm_{FECHA}.osm"
)
archivo_intermedio = (
    proyecto
    / "03_datos_intermedios"
    / "trazados"
    / f"R002_trazado_ida_continuo_{FECHA}.geojson"
)

nodos_acceso, referencias_acceso, etiquetas_acceso = leer_via(
    archivo_acceso, ID_VIA_ACCESO
)
nodos_principal, referencias_principal, etiquetas_principal = leer_via(
    archivo_principal, ID_VIA_PRINCIPAL
)

assert referencias_acceso[0] == NODO_INICIO
assert referencias_acceso[-1] == NODO_UNION
assert referencias_principal[0] == NODO_FIN
assert referencias_principal[-1] == NODO_UNION
assert etiquetas_acceso.get("highway") == "path"
assert etiquetas_principal.get("highway") == "path"

# La vía principal está orientada desde el extremo alto hacia el nodo de unión.
# Se invierte y se elimina el nodo compartido duplicado para formar una cadena.
referencias_principal_orientadas = list(reversed(referencias_principal))
referencias_unidas = referencias_acceso + referencias_principal_orientadas[1:]
nodos = {**nodos_acceso, **nodos_principal}
coordenadas = [nodos[referencia] for referencia in referencias_unidas]
geometria = LineString(coordenadas)

resultado = gpd.GeoDataFrame(
    [
        {
            "id_ruta": "R002",
            "nombre": "Sendero Los Pantzas",
            "vias_osm": f"{ID_VIA_ACCESO}|{ID_VIA_PRINCIPAL}",
            "nodo_inicio": NODO_INICIO,
            "nodo_union": NODO_UNION,
            "nodo_fin": NODO_FIN,
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

print("Archivos originales:", archivo_acceso.name, "|", archivo_principal.name)
print("Vías utilizadas:", ID_VIA_ACCESO, "|", ID_VIA_PRINCIPAL)
print("Nodos del acceso:", len(referencias_acceso))
print("Nodos del tramo principal:", len(referencias_principal))
print("Nodos de la cadena sin duplicar la unión:", len(referencias_unidas))
print("Geometría resultante:", comprobacion.geometry.iloc[0].geom_type)
print("Geometría válida:", comprobacion.geometry.iloc[0].is_valid)
print("Geometría simple:", comprobacion.geometry.iloc[0].is_simple)
print("Distancia de ida:", round(distancia_km, 3), "km")
print("Distancia preliminar de ida y vuelta:", round(distancia_km * 2, 3), "km")

assert archivo_acceso.exists()
assert archivo_principal.exists()
assert set(referencias_acceso) & set(referencias_principal) == {NODO_UNION}
assert len(referencias_unidas) == len(set(referencias_unidas))
assert len(comprobacion) == 1
assert comprobacion.crs.to_epsg() == 4326
assert comprobacion.geometry.iloc[0].geom_type == "LineString"
assert comprobacion.geometry.iloc[0].is_valid
assert comprobacion.geometry.iloc[0].is_simple

print("Trazado intermedio de R002 guardado y validado correctamente")
