"""Extrae Ruta 2 a Cascada La Reina del OSM original de R005, sin alterarlo."""

from pathlib import Path
from hashlib import sha256
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
ORIGINAL = RAIZ / "02_datos_originales/trazados/R005_nambillo_osm_2026-10-01.osm"
SALIDA = RAIZ / "03_datos_intermedios/trazados/R019_trazado_ida_continuo_2026-10-12.geojson"
ID_VIA = "31543544"
LAT_REINA = -0.093741
LON_REINA = -78.754425


def main() -> None:
    assert sha256(ORIGINAL.read_bytes()).hexdigest().upper() == (
        "6ED642B3EA7BBD358CC65C19627519B688ED5BA40A084ADF450068BA2C785BE3"
    ), "El extracto OSM original cambió; revisar procedencia antes de reprocesar"
    raiz = ET.parse(ORIGINAL).getroot()
    nodos = {n.attrib["id"]: n for n in raiz.findall("node")}
    via = next(w for w in raiz.findall("way") if w.attrib["id"] == ID_VIA)
    tags = {t.attrib["k"]: t.attrib["v"] for t in via.findall("tag")}
    assert tags.get("name") == "Ruta 2"
    assert tags.get("highway") == "footway"
    referencias = [nd.attrib["ref"] for nd in via.findall("nd")]
    assert len(referencias) == len(set(referencias))
    geometria = LineString(
        [(float(nodos[ref].attrib["lon"]), float(nodos[ref].attrib["lat"])) for ref in referencias]
    )
    assert geometria.is_valid and geometria.is_simple
    proyeccion = Transformer.from_crs(4326, 32717, always_xy=True).transform
    longitud_m = transform(proyeccion, geometria).length
    final_m = transform(proyeccion, Point(geometria.coords[-1]))
    cascada_m = transform(proyeccion, Point(LON_REINA, LAT_REINA))
    distancia_destino_m = final_m.distance(cascada_m)
    assert 2300 <= longitud_m <= 2360
    assert distancia_destino_m < 50
    gdf = gpd.GeoDataFrame(
        [{
            "id_ruta": "R019",
            "nombre": "Sendero Tarabita - Cascada La Reina",
            "id_via_osm": ID_VIA,
            "nombre_osm": tags["name"],
            "nodo_inicio": referencias[0],
            "nodo_fin": referencias[-1],
            "tipo_recorrido": "ida_y_vuelta",
            "estado": "via_osm_completa_contraste_destino_y_longitud",
            "fecha": "2026-10-12",
            "distancia_ida_km": round(longitud_m / 1000, 3),
            "distancia_fin_cascada_m": round(distancia_destino_m, 1),
            "geometry": geometria,
        }],
        crs="EPSG:4326",
    )
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(SALIDA, driver="GeoJSON")
    comprobacion = gpd.read_file(SALIDA)
    assert len(comprobacion) == 1
    assert comprobacion.geometry.iloc[0].is_simple
    print(
        f"R019: {len(referencias)} nodos; ida={longitud_m/1000:.3f} km; "
        f"ida y vuelta={2*longitud_m/1000:.3f} km; final-cascada={distancia_destino_m:.1f} m"
    )


if __name__ == "__main__":
    main()
