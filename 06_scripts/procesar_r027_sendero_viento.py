"""Extrae el Sendero del Viento de Moraspungo sin conectores por proximidad.

El extremo de la vía peatonal se usa como llegada al sector recreativo; el
mirador OSM, situado a unos 2 m, se conserva solo como referencia contextual.
"""

from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from pyproj import Geod


RAIZ = Path(__file__).resolve().parents[1]
FUENTE = RAIZ / "02_datos_originales/trazados/candidato_sendero_viento_moraspungo_osm_2026-10-22.osm"
SHA_FUENTE = "F225BD3C26933E60B91CD56C9C1064A9C8EE5BB67BC54733C4E5FD5174DE7414"
SALIDA = RAIZ / "03_datos_intermedios/trazados/R027_trazado_ida_continuo_2026-10-22.geojson"
VIA = "724818033"
VIA_ACCESO = "31263311"
NODO_INICIO = "347634309"
NODO_FIN = "6797699199"
NODO_MIRADOR_REFERENCIA = "6797709014"
GEOD = Geod(ellps="WGS84")


def construir() -> tuple[list[list[float]], dict]:
    contenido = FUENTE.read_bytes()
    if sha256(contenido).hexdigest().upper() != SHA_FUENTE:
        raise ValueError("Cambió el original OSM archivado del Sendero del Viento")
    raiz = ET.fromstring(contenido)
    nodos = {
        nodo.attrib["id"]: [float(nodo.attrib["lon"]), float(nodo.attrib["lat"])]
        for nodo in raiz.findall("node")
    }
    vias = {
        via.attrib["id"]: (
            [nd.attrib["ref"] for nd in via.findall("nd")],
            {tag.attrib["k"]: tag.attrib["v"] for tag in via.findall("tag")},
        )
        for via in raiz.findall("way")
    }
    refs, etiquetas = vias[VIA]
    acceso, etiquetas_acceso = vias[VIA_ACCESO]
    if etiquetas.get("highway") != "footway" or etiquetas.get("surface") != "paving_stones":
        raise ValueError("La vía ya no corresponde al sendero peatonal adoquinado")
    if etiquetas.get("access") == "no" or etiquetas.get("foot") == "no":
        raise ValueError("El acceso peatonal está restringido en OSM")
    if etiquetas_acceso.get("highway") != "unclassified" or NODO_INICIO not in acceso:
        raise ValueError("El inicio no coincide con la vía de acceso mapeada")
    if refs[0] != NODO_INICIO or refs[-1] != NODO_FIN or len(refs) != len(set(refs)):
        raise ValueError("La secuencia de nodos del sendero cambió")
    coords = [nodos[ref] for ref in refs]
    longitudes = GEOD.line_lengths([p[0] for p in coords], [p[1] for p in coords])
    largo_m = float(sum(longitudes))
    referencia = nodos[NODO_MIRADOR_REFERENCIA]
    _, _, separacion_m = GEOD.inv(*coords[-1], *referencia)
    if not 700 < largo_m < 760 or not 0 < separacion_m < 5:
        raise ValueError("La geometría no coincide con el recorrido revisado")
    return coords, {
        "refs": refs,
        "distancia_ida_km": round(largo_m / 1000, 3),
        "separacion_mirador_m": round(separacion_m, 1),
    }


def main() -> None:
    if SALIDA.exists():
        raise FileExistsError(f"El trazado ya existe: {SALIDA}")
    coords, datos = construir()
    objeto = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "id_ruta": "R027",
                "nombre": "Sendero del Viento - sector recreativo Moraspungo",
                "nodo_inicio": NODO_INICIO,
                "nodo_fin": NODO_FIN,
                "tipo_recorrido": "ida_y_vuelta",
                "fecha": "2026-10-22",
                "distancia_ida_km": datos["distancia_ida_km"],
            },
            "geometry": {"type": "LineString", "coordinates": coords},
        }],
    }
    SALIDA.write_text(json.dumps(objeto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"R027: {len(coords)} vértices; {datos['distancia_ida_km']:.3f} km de ida")


if __name__ == "__main__":
    main()
