"""Lectura validada de las rutas existentes para el prototipo cartográfico.

No asigna categorías de dificultad ni recomienda recorridos.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
TABLA = RAIZ / "07_resultados" / "tablas" / "dataset_clasificacion_rutas.csv"
TRAZADOS = RAIZ / "03_datos_intermedios" / "trazados"


def cargar_catalogo(tabla: Path = TABLA) -> list[dict[str, str]]:
    with tabla.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas or len({fila["id_ruta"] for fila in filas}) != len(filas):
        raise ValueError("El catálogo está vacío o contiene identificadores duplicados")
    return filas


def ruta_trazado(id_ruta: str, carpeta: Path = TRAZADOS) -> Path:
    if len(id_ruta) != 4 or id_ruta[0] != "R" or not id_ruta[1:].isdigit():
        raise ValueError("Identificador de ruta inválido")
    archivos = sorted(carpeta.glob(f"{id_ruta}_trazado_*.geojson"))
    if not archivos:
        raise FileNotFoundError(f"No existe trazado para {id_ruta}")
    # El piloto R001 conserva un trazado anterior: preferir el corte fechado más reciente.
    return max(archivos, key=lambda p: p.stem.rsplit("_", 1)[-1])


def cargar_trazado(id_ruta: str, carpeta: Path = TRAZADOS) -> tuple[dict, list[tuple[float, float]]]:
    archivo = ruta_trazado(id_ruta, carpeta)
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    entidades = datos.get("features", [])
    if datos.get("type") != "FeatureCollection" or len(entidades) != 1:
        raise ValueError(f"{id_ruta}: se esperaba una sola línea GeoJSON")
    entidad = entidades[0]
    if entidad.get("geometry", {}).get("type") != "LineString":
        raise ValueError(f"{id_ruta}: geometría no lineal")
    if entidad.get("properties", {}).get("id_ruta") != id_ruta:
        raise ValueError(f"{id_ruta}: el identificador no coincide con el archivo")
    coordenadas = entidad["geometry"].get("coordinates", [])
    if len(coordenadas) < 2:
        raise ValueError(f"{id_ruta}: faltan puntos del trazado")
    puntos = []
    for punto in coordenadas:
        if len(punto) < 2:
            raise ValueError(f"{id_ruta}: coordenada incompleta")
        lon, lat = float(punto[0]), float(punto[1])
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError(f"{id_ruta}: coordenada fuera de rango")
        puntos.append((lat, lon))
    return datos, puntos


def gpx_desde_puntos(id_ruta: str, nombre: str, puntos: list[tuple[float, float]]) -> bytes:
    """Exporta únicamente geometría 2D; no inventa elevación ni tiempos."""
    if len(puntos) < 2:
        raise ValueError("Se requieren al menos dos puntos")
    espacio = "http://www.topografix.com/GPX/1/1"
    ET.register_namespace("", espacio)
    raiz = ET.Element(f"{{{espacio}}}gpx", version="1.1", creator="Tesis trekking Pichincha")
    track = ET.SubElement(raiz, f"{{{espacio}}}trk")
    ET.SubElement(track, f"{{{espacio}}}name").text = f"{id_ruta} - {nombre}"
    segmento = ET.SubElement(track, f"{{{espacio}}}trkseg")
    for lat, lon in puntos:
        ET.SubElement(segmento, f"{{{espacio}}}trkpt", lat=str(lat), lon=str(lon))
    return ET.tostring(raiz, encoding="utf-8", xml_declaration=True)


def recorrido_para_animacion(
    puntos: list[tuple[float, float]], circular: bool
) -> list[tuple[float, float]]:
    """Reconstruye la vuelta por el mismo eje solo para la simulación visual.

    La geometría de retorno no es un registro de campo independiente.
    """
    if len(puntos) < 2:
        raise ValueError("Se requieren al menos dos puntos")
    if circular:
        return list(puntos)
    return list(puntos) + list(reversed(puntos[:-1]))
