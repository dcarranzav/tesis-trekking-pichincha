"""Procesa la vía OSM directa hacia Cascada Guagrapamba sin añadir conectores."""

from hashlib import sha256
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import transform


RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "02_datos_originales/trazados/candidato_guagrapamba_osm_2026-10-21.osm"
SALIDA = RAIZ / "03_datos_intermedios/trazados/R023_trazado_ida_continuo_2026-10-21.geojson"
SHA_FUENTE = "08223B3A9765EACF006A18DB9C7768A2C5ABE7F571F24EDFE1B11E12B746FD14"
ID_VIA = "1075564180"
ID_CASCADA = "8146768136"
ID_PARQUEADERO = "1205649963"


def construir() -> tuple[LineString, dict]:
    contenido = FUENTE.read_bytes()
    if sha256(contenido).hexdigest().upper() != SHA_FUENTE:
        raise ValueError("El original OSM de Guagrapamba cambió")
    raiz = ET.fromstring(contenido)
    nodos = {n.attrib["id"]: n for n in raiz.findall("node")}
    vias = {v.attrib["id"]: v for v in raiz.findall("way")}
    via = vias[ID_VIA]
    refs = [nd.attrib["ref"] for nd in via.findall("nd")]
    etiquetas = {t.attrib["k"]: t.attrib["v"] for t in via.findall("tag")}
    if etiquetas != {"highway": "path"} or len(refs) != 26 or refs[-1] != ID_CASCADA:
        raise ValueError("La vía peatonal o su extremo de cascada no coincide con el original revisado")
    if len(set(refs)) != len(refs):
        raise ValueError("La vía contiene nodos repetidos")
    cascada = {t.attrib["k"]: t.attrib["v"] for t in nodos[ID_CASCADA].findall("tag")}
    if cascada.get("name") != "Cascada Guagrapamba" or cascada.get("waterway") != "waterfall":
        raise ValueError("No se identificó inequívocamente la cascada")
    coords = [(float(nodos[ref].attrib["lon"]), float(nodos[ref].attrib["lat"])) for ref in refs]
    linea = LineString(coords)
    if not linea.is_valid or not linea.is_simple:
        raise ValueError("El sendero no es una línea simple válida")
    proyectar = Transformer.from_crs(4326, 32717, always_xy=True).transform
    linea_m = transform(proyectar, linea)
    if not 1600 < linea_m.length < 1750:
        raise ValueError("Longitud de sendero incompatible con el original revisado")
    parqueadero = vias[ID_PARQUEADERO]
    tags_parqueadero = {t.attrib["k"]: t.attrib["v"] for t in parqueadero.findall("tag")}
    if tags_parqueadero.get("amenity") != "parking" or "Guangrapamba" not in tags_parqueadero.get("name", ""):
        raise ValueError("No se identificó el parqueadero próximo")
    refs_parqueadero = [nd.attrib["ref"] for nd in parqueadero.findall("nd")]
    puntos_parqueadero = [proyectar(float(nodos[ref].attrib["lon"]), float(nodos[ref].attrib["lat"]))
                          for ref in refs_parqueadero]
    poligono = Polygon(puntos_parqueadero)
    distancia_inicio_m = transform(proyectar, Point(coords[0])).distance(poligono)
    if not 0 <= distancia_inicio_m < 30:
        raise ValueError("El inicio no está próximo al parqueadero")
    return linea, {"refs": refs, "distancia_ida_km": round(linea_m.length / 1000, 3),
                   "distancia_inicio_parqueadero_m": round(distancia_inicio_m, 1)}


def main() -> None:
    if SALIDA.exists():
        raise FileExistsError(f"El trazado R023 ya existe: {SALIDA}")
    linea, datos = construir()
    gdf = gpd.GeoDataFrame([{
        "id_ruta": "R023",
        "nombre": "Sendero a Cascada Guagrapamba",
        "id_via_osm": ID_VIA,
        "nodo_inicio": datos["refs"][0],
        "nodo_fin": ID_CASCADA,
        "tipo_recorrido": "ida_y_vuelta",
        "fecha": "2026-10-21",
        "distancia_ida_km": datos["distancia_ida_km"],
        "distancia_inicio_parqueadero_m": datos["distancia_inicio_parqueadero_m"],
        "geometry": linea,
    }], crs="EPSG:4326")
    gdf.to_file(SALIDA, driver="GeoJSON")
    print(f"R023: {len(datos['refs'])} vértices; {datos['distancia_ida_km']:.3f} km de ida; "
          f"inicio a {datos['distancia_inicio_parqueadero_m']:.1f} m del parqueadero")


if __name__ == "__main__":
    main()
