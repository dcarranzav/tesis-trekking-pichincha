"""Diagnostica GPX públicos sin incorporarlos al inventario ni redistribuirlos.

Uso: python 06_scripts/evaluar_trazas_gpx_externas.py archivo1.gpx [archivo2.gpx ...]
La salida es descriptiva: la identidad, el acceso y la licencia requieren revisión.
"""

from argparse import ArgumentParser
from pathlib import Path
import hashlib
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import transform


RAIZ = Path(__file__).resolve().parents[1]
TRAZADOS = RAIZ / "03_datos_intermedios" / "trazados"
PROYECTAR = Transformer.from_crs(4326, 32717, always_xy=True).transform


def leer_segmentos(ruta: Path) -> list[LineString]:
    raiz = ET.parse(ruta).getroot()
    segmentos = []
    for elemento in raiz.iter():
        if elemento.tag.rsplit("}", 1)[-1] not in ("trkseg", "rte"):
            continue
        puntos = [
            (float(hijo.attrib["lon"]), float(hijo.attrib["lat"]))
            for hijo in elemento
            if hijo.tag.rsplit("}", 1)[-1] in ("trkpt", "rtept")
        ]
        if len(puntos) >= 2:
            segmentos.append(LineString(puntos))
    return segmentos


def geometria_actual(id_ruta: str):
    archivos = sorted(TRAZADOS.glob(f"{id_ruta}_trazado_*.geojson"))
    if not archivos:
        return None
    # Solo se comparan rutas con una única versión. No se escoge una
    # silenciosamente si el inventario contiene varias geometrías históricas.
    if len(archivos) != 1:
        print(f"  {id_ruta}: {len(archivos)} versiones; comparación omitida")
        return None
    geodatos = gpd.read_file(archivos[0]).to_crs(32717)
    return geodatos.geometry.iloc[0]


def describir(ruta: Path) -> None:
    segmentos = leer_segmentos(ruta)
    print(f"\n{ruta.name}")
    print(f"  sha256: {hashlib.sha256(ruta.read_bytes()).hexdigest()}")
    print(f"  segmentos: {len(segmentos)}")
    if not segmentos:
        return
    lineas = [transform(PROYECTAR, segmento) for segmento in segmentos]
    for indice, linea in enumerate(lineas, 1):
        puntos = len(segmentos[indice - 1].coords)
        saltos = [
            Point(a).distance(Point(b))
            for a, b in zip(list(linea.coords)[:-1], list(linea.coords)[1:])
        ]
        longitud_recta_max = max(saltos)
        print(
            f"  segmento {indice}: {puntos} puntos, {linea.length / 1000:.3f} km, "
            f"salto máximo {longitud_recta_max:.1f} m, "
            f"saltos >100 m={sum(s > 100 for s in saltos)}, "
            f">250 m={sum(s > 250 for s in saltos)}, simple={linea.is_simple}"
        )
        inicio = segmentos[indice - 1].coords[0]
        fin = segmentos[indice - 1].coords[-1]
        print(f"    inicio lon/lat: {inicio[0]:.6f},{inicio[1]:.6f}")
        print(f"    final lon/lat: {fin[0]:.6f},{fin[1]:.6f}")
        print(f"    cierre: {Point(linea.coords[0]).distance(Point(linea.coords[-1])):.1f} m")
        for id_ruta in ("R004", "R008"):
            existente = geometria_actual(id_ruta)
            if existente is None:
                continue
            cubierto = linea.intersection(existente.buffer(20)).length / linea.length
            print(
                f"    frente a {id_ruta}: separación mínima {linea.distance(existente):.1f} m, "
                f"GPX dentro de 20 m {cubierto:.1%}"
            )


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("gpx", nargs="+", type=Path)
    args = parser.parse_args()
    for ruta in args.gpx:
        if not ruta.is_file():
            parser.error(f"No existe: {ruta}")
        describir(ruta)


if __name__ == "__main__":
    main()
