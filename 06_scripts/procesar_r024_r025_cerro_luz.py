"""Construye los dos recorridos OSM al Mirador Cerro de la Luz (Puéllaro) sin añadir conectores.

R024: sendero directo (vía 1209333234). R025: sendero superior (vías 1421205625 y 1421205624) y tramo final
de 1209333234. Todos los empalmes son nodos OSM compartidos; no se une nada por cercanía.
"""

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
from shapely.geometry import LineString
from shapely.ops import transform


RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "02_datos_originales/trazados/candidato_cerro_luz_puellaro_osm_2026-10-21.osm"
SHA_FUENTE = "B021608EFC1FAEEF530C2B96976472C3B607498A6FCC242BB56224CFE76652FB"
NODO_MIRADOR = "11204680653"
NODO_INICIO = "13060067399"  # empalme del sendero con la vía «Entrada al Bosque Magico» (877695136)
NODO_EMPALME_DIRECTO = "13060067403"
NODO_EMPALME_SUPERIOR = "13060067262"
NODO_FIN_SUPERIOR = "13060067207"
VIA_ACCESO = "877695136"
SALIDAS = {
    "R024": RAIZ / "03_datos_intermedios/trazados/R024_trazado_ida_continuo_2026-10-21.geojson",
    "R025": RAIZ / "03_datos_intermedios/trazados/R025_trazado_ida_continuo_2026-10-21.geojson",
}
NOMBRES = {
    "R024": "Cerro de la Luz - sendero directo al mirador",
    "R025": "Cerro de la Luz - sendero superior al mirador",
}


def _leer() -> tuple[dict, dict, dict]:
    contenido = FUENTE.read_bytes()
    if sha256(contenido).hexdigest().upper() != SHA_FUENTE:
        raise ValueError("El original OSM de Cerro de la Luz cambió")
    raiz = ET.fromstring(contenido)
    nodos = {n.attrib["id"]: (float(n.attrib["lon"]), float(n.attrib["lat"])) for n in raiz.findall("node")}
    etiquetas_nodo = {n.attrib["id"]: {t.attrib["k"]: t.attrib["v"] for t in n.findall("tag")} for n in raiz.findall("node")}
    vias = {
        v.attrib["id"]: ([nd.attrib["ref"] for nd in v.findall("nd")], {t.attrib["k"]: t.attrib["v"] for t in v.findall("tag")})
        for v in raiz.findall("way")
    }
    return nodos, etiquetas_nodo, vias


def _largo_m(coords: list[tuple[float, float]]) -> float:
    proyectar = Transformer.from_crs(4326, 32617, always_xy=True).transform
    return transform(proyectar, LineString(coords)).length


def construir() -> dict[str, tuple[LineString, dict]]:
    nodos, etiquetas_nodo, vias = _leer()
    mirador = etiquetas_nodo[NODO_MIRADOR]
    if mirador.get("name") != "CERRO DE LA LUZ" or "MIRADOR" not in mirador.get("official_name", "").upper():
        raise ValueError("No se identificó inequívocamente el mirador")
    directo, t_directo = vias["1209333234"]
    superior_a, t_a = vias["1421205625"]
    superior_b, t_b = vias["1421205624"]
    acceso_refs, t_acceso = vias[VIA_ACCESO]
    if t_directo.get("highway") != "path" or t_a.get("highway") != "footway" or t_b.get("highway") != "footway":
        raise ValueError("Las vías del sendero no son peatonales")
    if directo[-1] != NODO_MIRADOR or directo[0] != NODO_EMPALME_DIRECTO:
        raise ValueError("La vía directa no termina en el mirador")
    if superior_a[-1] != NODO_INICIO or NODO_INICIO not in acceso_refs:
        raise ValueError("El inicio no es un nodo compartido con la vía de acceso")
    if t_acceso.get("highway") != "residential":
        raise ValueError("La vía de acceso cambió")
    # R024: empalme con la vía de acceso -> 13060067403 (por 1421205625) -> mirador (por 1209333234)
    tramo_acceso = superior_a[superior_a.index(NODO_EMPALME_DIRECTO):][::-1]  # inicio -> empalme directo
    if tramo_acceso[0] != NODO_INICIO:
        raise ValueError("El empalme directo no es contiguo al inicio")
    refs_r024 = tramo_acceso + directo[1:]
    # R025: inicio -> 13060067262 por 1421205625 invertida -> 13060067207 por 1421205624 -> mirador por el final de 1209333234
    primero = superior_a[::-1]
    if primero[-1] != NODO_EMPALME_SUPERIOR:
        raise ValueError("El sendero superior no llega al empalme esperado")
    i_emp = superior_b.index(NODO_EMPALME_SUPERIOR)
    i_fin = superior_b.index(NODO_FIN_SUPERIOR)
    segundo = superior_b[i_fin:i_emp + 1][::-1] if i_fin < i_emp else superior_b[i_emp:i_fin + 1]
    if segundo[0] != NODO_EMPALME_SUPERIOR or segundo[-1] != NODO_FIN_SUPERIOR:
        raise ValueError("El tramo superior no une los empalmes esperados")
    final = directo[directo.index(NODO_FIN_SUPERIOR):]
    refs_r025 = primero + segundo[1:] + final[1:]
    resultados = {}
    for id_ruta, refs, rango in (("R024", refs_r024, (490, 520)), ("R025", refs_r025, (1240, 1300))):
        if len(set(refs)) != len(refs):
            raise ValueError(f"{id_ruta} repite nodos")
        coords = [nodos[ref] for ref in refs]
        linea = LineString(coords)
        if not linea.is_valid or not linea.is_simple:
            raise ValueError(f"{id_ruta} no es una línea simple válida")
        largo = _largo_m(coords)
        if not rango[0] < largo < rango[1] or refs[0] != NODO_INICIO or refs[-1] != NODO_MIRADOR:
            raise ValueError(f"{id_ruta} no coincide con el original revisado")
        resultados[id_ruta] = (linea, {"refs": refs, "distancia_ida_km": round(largo / 1000, 3)})
    comunes = set(refs_r024) & set(refs_r025)
    if len(comunes) > 0.15 * len(refs_r024) + 6:
        raise ValueError("Las variantes comparten demasiado trazado")
    return resultados


def main() -> None:
    for salida in SALIDAS.values():
        if salida.exists():
            raise FileExistsError(f"El trazado ya existe: {salida}")
    for id_ruta, (linea, datos) in construir().items():
        gdf = gpd.GeoDataFrame([{
            "id_ruta": id_ruta,
            "nombre": NOMBRES[id_ruta],
            "nodo_inicio": datos["refs"][0],
            "nodo_fin": NODO_MIRADOR,
            "tipo_recorrido": "ida_y_vuelta",
            "fecha": "2026-10-21",
            "distancia_ida_km": datos["distancia_ida_km"],
            "geometry": linea,
        }], crs="EPSG:4326")
        gdf.to_file(SALIDAS[id_ruta], driver="GeoJSON")
        print(f"{id_ruta}: {len(datos['refs'])} vértices; {datos['distancia_ida_km']:.3f} km de ida")


if __name__ == "__main__":
    main()
