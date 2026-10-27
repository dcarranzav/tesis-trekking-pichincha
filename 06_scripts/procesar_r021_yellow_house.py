"""Construye la variante Yellow House por los Senderos 1 y 2 desde Overpass.

El JSON original se conserva intacto. Los desvíos sustituyen únicamente los
tramos de la vía principal comprendidos entre nodos OSM compartidos.
"""

from hashlib import sha256
import json
from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString
from shapely.ops import transform


RAIZ = Path(__file__).resolve().parents[1]
ORIGINAL = RAIZ / "02_datos_originales/trazados/Yellow_House_variantes_overpass_2026-10-17.json"
SALIDA = RAIZ / "03_datos_intermedios/trazados/R021_trazado_ida_continuo_2026-10-17.geojson"
VIA_PRINCIPAL = 299595681
DESVIOS = (301132246, 301132249)


def cargar_vias() -> dict[int, dict]:
    documento = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    vias = {via["id"]: via for via in documento["elements"]}
    assert set(vias) >= {VIA_PRINCIPAL, *DESVIOS}
    assert vias[VIA_PRINCIPAL]["tags"]["name"] == "Yellow House Trail"
    for numero, id_via in enumerate(DESVIOS, 1):
        assert vias[id_via]["tags"]["name"] == f"Sendero {numero}"
        assert vias[id_via]["tags"]["highway"] == "footway"
    for via in vias.values():
        assert len(via["nodes"]) == len(via["geometry"])
    return vias


def coordenadas(via: dict) -> list[tuple[float, float]]:
    return [(p["lon"], p["lat"]) for p in via["geometry"]]


def construir(vias: dict[int, dict]) -> tuple[LineString, dict]:
    principal = vias[VIA_PRINCIPAL]
    refs = principal["nodes"]
    coords = coordenadas(principal)
    uniones = {}
    # Orden descendente: los índices de los tramos anteriores no se desplazan.
    for id_via in reversed(DESVIOS):
        desvio = vias[id_via]
        compartidos = set(desvio["nodes"]) & set(refs)
        assert compartidos == {desvio["nodes"][0], desvio["nodes"][-1]}
        inicio, fin = sorted(refs.index(nodo) for nodo in compartidos)
        segmento = coordenadas(desvio)
        if desvio["nodes"][0] != refs[inicio]:
            segmento.reverse()
        assert segmento[0] == coords[inicio] and segmento[-1] == coords[fin]
        uniones[id_via] = [refs[inicio], refs[fin]]
        coords = coords[: inicio + 1] + segmento[1:-1] + coords[fin:]
    assert len(coords) == len(set(coords))
    linea = LineString(coords)
    assert linea.is_valid and linea.is_simple
    assert coords[0] == coordenadas(principal)[0]
    assert coords[-1] == coordenadas(principal)[-1]
    return linea, uniones


def main() -> None:
    vias = cargar_vias()
    linea, uniones = construir(vias)
    proyeccion = Transformer.from_crs(4326, 32717, always_xy=True).transform
    principal_m = transform(proyeccion, LineString(coordenadas(vias[VIA_PRINCIPAL])))
    variante_m = transform(proyeccion, linea)
    cobertura_principal = principal_m.intersection(variante_m.buffer(20)).length / principal_m.length
    cobertura_variante = variante_m.intersection(principal_m.buffer(20)).length / variante_m.length
    assert 2850 < variante_m.length < 2950
    assert cobertura_principal < 0.90 and cobertura_variante < 0.90
    gdf = gpd.GeoDataFrame(
        [{
            "id_ruta": "R021",
            "nombre": "Yellow House Trail vía Senderos 1 y 2",
            "id_vias_osm": "299595681|301132246|301132249",
            "nodo_inicio": str(vias[VIA_PRINCIPAL]["nodes"][0]),
            "nodo_fin": str(vias[VIA_PRINCIPAL]["nodes"][-1]),
            "tipo_recorrido": "ida_y_vuelta",
            "fecha": "2026-10-17",
            "distancia_ida_km": round(variante_m.length / 1000, 3),
            "cobertura_r017_20m": round(cobertura_principal, 3),
            "cobertura_r021_20m": round(cobertura_variante, 3),
            "geometry": linea,
        }],
        crs="EPSG:4326",
    )
    if SALIDA.exists():
        raise FileExistsError(f"El trazado ya existe: {SALIDA}")
    gdf.to_file(SALIDA, driver="GeoJSON")
    print("SHA-256 original:", sha256(ORIGINAL.read_bytes()).hexdigest().upper())
    print("Nodos compartidos:", uniones)
    print(f"R021: {len(linea.coords)} vértices, {variante_m.length/1000:.3f} km de ida")
    print(f"Coberturas frente a R017: {cobertura_principal:.3f} / {cobertura_variante:.3f}")


if __name__ == "__main__":
    main()
