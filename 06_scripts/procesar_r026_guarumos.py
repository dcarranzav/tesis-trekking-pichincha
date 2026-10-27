"""Construye el recorrido OSM de ida desde la estación de desembarque de la tarabita hasta la Cascada Guarumos.

La ruta usa solo nodos OSM compartidos entre las vías `Ruta 1` (964152743), `Ruta 3` (196510810), 497709953 y el
ramal final 301136576. No se añade ningún conector por proximidad. La estación (nodo 352972925) es la lejana respecto
de la carretera, la misma desde la que parten R005 y R019. Cascada Colibríes comparte este trazado salvo 44 m finales
y no se modela como ruta aparte.
"""

from hashlib import sha256
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

from pyproj import Transformer
from shapely.geometry import LineString
from shapely.ops import transform


RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "02_datos_originales/trazados/candidato_guarumos_colibries_mindo_osm_2026-10-22.osm"
SHA_FUENTE = "09C8383A0DD356D9D33860C74E006FE637C0E976CA182B33C79927E35B61F0EC"
NODO_INICIO = "352972925"  # estación de desembarque de la tarabita (aerialway=station)
NODO_DESTINO = "3047618576"  # Cascada Guarumos
NODO_BIFURCACION = "3052416447"  # Colibríes queda a 44 m por otro ramal desde este nodo
VIA_TARABITA = "193975746"
VIAS_RECORRIDO = ["964152743", "196510810", "497709953", "301136576"]
SALIDA = RAIZ / "03_datos_intermedios/trazados/R026_trazado_ida_continuo_2026-10-22.geojson"
NOMBRE = "Tarabita - Cascada Guarumos"


def _leer() -> tuple[dict, dict, dict]:
    contenido = FUENTE.read_bytes()
    if sha256(contenido).hexdigest().upper() != SHA_FUENTE:
        raise ValueError("El original OSM de Guarumos/Colibríes cambió")
    raiz = ET.fromstring(contenido)
    nodos = {n.attrib["id"]: (float(n.attrib["lon"]), float(n.attrib["lat"])) for n in raiz.findall("node")}
    etiquetas = {n.attrib["id"]: {t.attrib["k"]: t.attrib["v"] for t in n.findall("tag")} for n in raiz.findall("node")}
    vias = {
        v.attrib["id"]: ([nd.attrib["ref"] for nd in v.findall("nd")], {t.attrib["k"]: t.attrib["v"] for t in v.findall("tag")})
        for v in raiz.findall("way")
    }
    return nodos, etiquetas, vias


def _largo_m(coords: list[tuple[float, float]]) -> float:
    proyectar = Transformer.from_crs(4326, 32717, always_xy=True).transform
    return transform(proyectar, LineString(coords)).length


def construir() -> tuple[LineString, dict]:
    nodos, etiquetas, vias = _leer()
    if etiquetas[NODO_INICIO].get("aerialway") != "yes" or etiquetas[NODO_INICIO].get("public_transport") != "station":
        raise ValueError("El nodo inicial no es una estación de la tarabita")
    if etiquetas[NODO_DESTINO].get("name") != "Cascada Guarumos" or etiquetas[NODO_DESTINO].get("waterway") != "waterfall":
        raise ValueError("El nodo destino no es Cascada Guarumos")
    cable, t_cable = vias[VIA_TARABITA]
    if t_cable.get("aerialway") != "cable_car" or NODO_INICIO not in cable:
        raise ValueError("La estación no pertenece a la línea de la tarabita")
    for via in VIAS_RECORRIDO:
        t = vias[via][1]
        if t.get("highway") != "footway" or t.get("access") == "no" or t.get("foot") == "no":
            raise ValueError(f"La vía {via} no es utilizable a pie")
    refs = [NODO_INICIO]
    actual = NODO_INICIO
    for i, via in enumerate(VIAS_RECORRIDO):
        ids = vias[via][0]
        if actual not in ids:
            raise ValueError(f"El nodo {actual} no pertenece a la vía {via}")
        if i + 1 < len(VIAS_RECORRIDO):
            siguiente = vias[VIAS_RECORRIDO[i + 1]][0]
            comunes = [n for n in ids if n in siguiente]
            if not comunes:
                raise ValueError(f"Las vías {via} y {VIAS_RECORRIDO[i + 1]} no comparten nodo")
            destino_tramo = min(comunes, key=lambda n: abs(ids.index(n) - ids.index(actual)))
        else:
            destino_tramo = NODO_DESTINO
        a, b = ids.index(actual), ids.index(destino_tramo)
        tramo = ids[a:b + 1] if a <= b else ids[b:a + 1][::-1]
        refs += tramo[1:]
        actual = destino_tramo
    if actual != NODO_DESTINO or len(set(refs)) != len(refs):
        raise ValueError("El recorrido no llega a Guarumos o repite nodos")
    if NODO_BIFURCACION not in refs:
        raise ValueError("El recorrido no pasa por el nodo de bifurcación esperado")
    coords = [nodos[r] for r in refs]
    linea = LineString(coords)
    if not linea.is_valid or not linea.is_simple:
        raise ValueError("El recorrido no es una línea simple válida")
    largo = _largo_m(coords)
    if not 1060 < largo < 1075:
        raise ValueError("La longitud no coincide con el original revisado")
    return linea, {"refs": refs, "distancia_ida_km": round(largo / 1000, 3)}


def main() -> None:
    import geopandas as gpd

    if SALIDA.exists():
        raise FileExistsError(f"El trazado ya existe: {SALIDA}")
    linea, datos = construir()
    gdf = gpd.GeoDataFrame([{
        "id_ruta": "R026",
        "nombre": NOMBRE,
        "nodo_inicio": NODO_INICIO,
        "nodo_fin": NODO_DESTINO,
        "tipo_recorrido": "ida_y_vuelta",
        "fecha": "2026-10-22",
        "distancia_ida_km": datos["distancia_ida_km"],
        "geometry": linea,
    }], crs="EPSG:4326")
    gdf.to_file(SALIDA, driver="GeoJSON")
    print(f"R026: {len(datos['refs'])} vértices; {datos['distancia_ida_km']:.3f} km de ida")


if __name__ == "__main__":
    main()
