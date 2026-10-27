"""Construye la candidata a la Cruz del Ilaló desde la captura OSM normalizada.

No añade un enlace artificial hasta el marcador de la cruz. La fuente no es
el XML original: esa limitación se conserva explícitamente en el registro.
"""

from hashlib import sha256
import json
import os
from pathlib import Path
import sys

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import transform


RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "02_datos_originales/trazados/R022_ilalo_cruz_overpass_snapshot_2026-10-17.json"
SALIDA = RAIZ / "03_datos_intermedios/trazados/R022_trazado_ida_continuo_2026-10-17.geojson"
HASH_FUENTE = "6C1C1056DC33D3060116BC6B5F48628BF9B8314F2698C487DEB7B666B708FA32"


def construir(documento: dict) -> tuple[LineString, list[int], float]:
    via = documento["way"]
    poi = documento["poi"]
    refs = via["nodes"]
    coords = via["geometry"]
    assert via["id"] == 297582904
    assert via["tags"] == {
        "highway": "path", "name": "camino a la Cruz del Ilaló",
        "sac_scale": "hiking", "surface": "earth",
    }
    assert len(refs) == len(coords) == 128 and len(set(refs)) == len(refs)
    assert (refs[0], refs[-1]) == (1323665115, 1369911783)
    assert poi["id"] == 4393010962 and poi["tags"]["name"] == "Cruz del Ilaló"
    linea = LineString(reversed(coords))  # Inicio: calle Los Olivos; final: cerca de la cruz.
    assert linea.is_valid and linea.is_simple
    proy = Transformer.from_crs(4326, 32717, always_xy=True).transform
    longitud_m = transform(proy, linea).length
    distancia_poi_m = transform(proy, Point(linea.coords[-1])).distance(
        transform(proy, Point(poi["lon"], poi["lat"]))
    )
    assert 2100 < longitud_m < 2300
    assert distancia_poi_m < 10
    return linea, list(reversed(refs)), distancia_poi_m


def main() -> None:
    if SALIDA.exists():
        raise FileExistsError(f"El trazado ya existe: {SALIDA}")
    contenido = FUENTE.read_bytes()
    assert sha256(contenido).hexdigest().upper() == HASH_FUENTE
    documento = json.loads(contenido)
    linea, refs, distancia_poi_m = construir(documento)
    proy = Transformer.from_crs(4326, 32717, always_xy=True).transform
    longitud_m = transform(proy, linea).length
    gdf = gpd.GeoDataFrame([{
        "id_ruta": "R022",
        "nombre": "Camino a la Cruz del Ilaló desde Los Olivos",
        "id_via_osm": "297582904",
        "nodo_inicio": str(refs[0]),
        "nodo_fin": str(refs[-1]),
        "tipo_recorrido": "ida_y_vuelta",
        "fecha": "2026-10-17",
        "distancia_ida_km": round(longitud_m / 1000, 3),
        "distancia_fin_cruz_m": round(distancia_poi_m, 1),
        "fuente_normalizada": FUENTE.name,
        "geometry": linea,
    }], crs="EPSG:4326")
    gdf.to_file(SALIDA, driver="GeoJSON")
    assert gpd.read_file(SALIDA).geometry.iloc[0].is_simple
    print(f"R022: {len(refs)} vértices; ida={longitud_m/1000:.3f} km; fin-cruz={distancia_poi_m:.1f} m")


if __name__ == "__main__":
    main()
