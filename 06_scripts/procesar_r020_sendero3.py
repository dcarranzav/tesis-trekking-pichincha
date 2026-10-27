"""Construye una variante continua de R017 por el Sendero 3 de Yellow House."""

from hashlib import sha256
from pathlib import Path
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString
from shapely.ops import transform


RAIZ = Path(__file__).resolve().parents[1]
ORIGINAL_PRINCIPAL = RAIZ / "02_datos_originales/trazados/R017_yellow_house_trail_osm_2026-10-09.osm"
ORIGINAL_DESVIO = RAIZ / "02_datos_originales/trazados/R020_yellow_house_sendero3_osm_2026-10-14.osm"
SALIDA = RAIZ / "03_datos_intermedios/trazados/R020_trazado_ida_continuo_2026-10-14.geojson"
HASH_PRINCIPAL = "4B7DE137541706B69F95BCF1C8EA22F58DAC687495209DC23379B98DEAEA5719"
HASH_DESVIO = "95853A03BC35A2DB2D56B98D7197C09761344AC662B600FE991C453889B2F66F"


def leer_via(archivo: Path, id_via: str, nombre: str) -> tuple[list[str], list[tuple[float, float]]]:
    raiz = ET.parse(archivo).getroot()
    nodos = {n.attrib["id"]: n for n in raiz.findall("node")}
    via = next(w for w in raiz.findall("way") if w.attrib["id"] == id_via)
    etiquetas = {t.attrib["k"]: t.attrib["v"] for t in via.findall("tag")}
    assert etiquetas.get("name") == nombre
    assert etiquetas.get("highway") in {"path", "footway"}
    referencias = [n.attrib["ref"] for n in via.findall("nd")]
    assert len(referencias) == len(set(referencias))
    puntos = [(float(nodos[r].attrib["lon"]), float(nodos[r].attrib["lat"])) for r in referencias]
    return referencias, puntos


def combinar(
    principal: tuple[list[str], list[tuple[float, float]]],
    desvio: tuple[list[str], list[tuple[float, float]]],
) -> LineString:
    refs_p, coords_p = principal
    refs_d, coords_d = desvio
    assert set(refs_p) & set(refs_d) == {refs_d[0], refs_d[-1]}
    indice_entrada = refs_p.index(refs_d[-1])
    indice_salida = refs_p.index(refs_d[0])
    assert indice_entrada < indice_salida
    coords = coords_p[: indice_entrada + 1] + list(reversed(coords_d[:-1])) + coords_p[indice_salida + 1 :]
    assert len(coords) == len(set(coords))
    linea = LineString(coords)
    assert linea.is_valid and linea.is_simple
    assert coords[0] == coords_p[0] and coords[-1] == coords_p[-1]
    return linea


def main() -> None:
    assert sha256(ORIGINAL_PRINCIPAL.read_bytes()).hexdigest().upper() == HASH_PRINCIPAL
    assert sha256(ORIGINAL_DESVIO.read_bytes()).hexdigest().upper() == HASH_DESVIO
    principal = leer_via(ORIGINAL_PRINCIPAL, "299595681", "Yellow House Trail")
    desvio = leer_via(ORIGINAL_DESVIO, "299595680", "Sendero 3")
    linea = combinar(principal, desvio)
    proyeccion = Transformer.from_crs(4326, 32717, always_xy=True).transform
    principal_m = transform(proyeccion, LineString(principal[1]))
    variante_m = transform(proyeccion, linea)
    cobertura_principal = principal_m.intersection(variante_m.buffer(20)).length / principal_m.length
    cobertura_variante = variante_m.intersection(principal_m.buffer(20)).length / variante_m.length
    assert 3300 < variante_m.length < 3340
    assert cobertura_principal < 0.90 and cobertura_variante < 0.90
    gdf = gpd.GeoDataFrame(
        [{
            "id_ruta": "R020",
            "nombre": "Yellow House Trail vía Sendero 3",
            "id_vias_osm": "299595681|299595680",
            "nodo_inicio": principal[0][0],
            "nodo_fin": principal[0][-1],
            "tipo_recorrido": "ida_y_vuelta",
            "fecha": "2026-10-14",
            "distancia_ida_km": round(variante_m.length / 1000, 3),
            "cobertura_r017_20m": round(cobertura_principal, 3),
            "cobertura_r020_20m": round(cobertura_variante, 3),
            "geometry": linea,
        }],
        crs="EPSG:4326",
    )
    if SALIDA.exists():
        raise FileExistsError(f"La geometría ya existe: {SALIDA}")
    gdf.to_file(SALIDA, driver="GeoJSON")
    comprobacion = gpd.read_file(SALIDA)
    assert len(comprobacion) == 1 and comprobacion.geometry.iloc[0].is_simple
    print(
        f"R020: {len(linea.coords)} nodos; ida={variante_m.length/1000:.3f} km; "
        f"coberturas R017={cobertura_principal:.3f}, R020={cobertura_variante:.3f}"
    )


if __name__ == "__main__":
    main()
