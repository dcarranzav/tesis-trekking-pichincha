"""Inspecciona metadatos y geometría básica de vías OSM sin guardarlas."""

from argparse import ArgumentParser
import math
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen


def distancia_haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = map(math.radians, a)
    lon2, lat2 = map(math.radians, b)
    delta_lon = lon2 - lon1
    delta_lat = lat2 - lat1
    termino = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * 6_371_008.8 * math.asin(math.sqrt(termino))


def inspeccionar(id_via: str) -> dict:
    url = f"https://api.openstreetmap.org/api/0.6/way/{id_via}/full"
    solicitud = Request(
        url,
        headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"},
    )
    with urlopen(solicitud, timeout=120) as respuesta:
        raiz = ET.parse(respuesta).getroot()

    nodos = {
        nodo.attrib["id"]: (float(nodo.attrib["lon"]), float(nodo.attrib["lat"]))
        for nodo in raiz.findall("node")
    }
    via = next(
        elemento
        for elemento in raiz.findall("way")
        if elemento.attrib["id"] == id_via
    )
    referencias = [nd.attrib["ref"] for nd in via.findall("nd")]
    coordenadas = [nodos[referencia] for referencia in referencias]
    etiquetas = {tag.attrib["k"]: tag.attrib["v"] for tag in via.findall("tag")}
    longitud_m = sum(
        distancia_haversine_m(inicio, fin)
        for inicio, fin in zip(coordenadas, coordenadas[1:])
    )
    centro_lon = sum(coordenada[0] for coordenada in coordenadas) / len(coordenadas)
    centro_lat = sum(coordenada[1] for coordenada in coordenadas) / len(coordenadas)
    return {
        "id": id_via,
        "nombre": etiquetas.get("name", ""),
        "highway": etiquetas.get("highway", ""),
        "sac_scale": etiquetas.get("sac_scale", ""),
        "surface": etiquetas.get("surface", ""),
        "nodos": len(referencias),
        "cerrada": referencias[0] == referencias[-1],
        "longitud_km": longitud_m / 1000,
        "centro_lat": centro_lat,
        "centro_lon": centro_lon,
        "primero": referencias[0],
        "ultimo": referencias[-1],
        "inicio_lat": coordenadas[0][1],
        "inicio_lon": coordenadas[0][0],
        "fin_lat": coordenadas[-1][1],
        "fin_lon": coordenadas[-1][0],
        "url": url,
    }


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("ids", nargs="+")
    argumentos = parser.parse_args()
    columnas = [
        "id",
        "nombre",
        "highway",
        "sac_scale",
        "surface",
        "nodos",
        "cerrada",
        "longitud_km",
        "centro_lat",
        "centro_lon",
        "primero",
        "ultimo",
        "inicio_lat",
        "inicio_lon",
        "fin_lat",
        "fin_lon",
        "url",
    ]
    print("\t".join(columnas))
    for id_via in argumentos.ids:
        fila = inspeccionar(id_via)
        valores = []
        for columna in columnas:
            valor = fila[columna]
            if isinstance(valor, float):
                valores.append(f"{valor:.6f}")
            else:
                valores.append(str(valor))
        print("\t".join(valores))


if __name__ == "__main__":
    main()
