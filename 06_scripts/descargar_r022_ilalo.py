"""Descarga sin sobrescribir la fuente OSM de la candidata Cruz del Ilaló.

Este paso no incorpora R022 al inventario: solo conserva la vía completa y
comprueba su identidad antes de cualquier cálculo altimétrico.
"""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
ID_VIA = "297582904"
URL = f"https://www.openstreetmap.org/api/0.6/way/{ID_VIA}/full"
SALIDA = RAIZ / "02_datos_originales/trazados/R022_ilalo_cruz_osm_2026-10-20.osm"


def validar(contenido: bytes) -> int:
    raiz = ET.fromstring(contenido)
    vias = [via for via in raiz.findall("way") if via.attrib.get("id") == ID_VIA]
    if len(vias) != 1:
        raise ValueError("No aparece exactamente una vez la vía esperada")
    via = vias[0]
    etiquetas = {tag.attrib["k"]: tag.attrib["v"] for tag in via.findall("tag")}
    if etiquetas.get("name") != "camino a la Cruz del Ilaló":
        raise ValueError("Nombre de la vía distinto al contrastado")
    if etiquetas.get("highway") != "path" or etiquetas.get("sac_scale") != "hiking":
        raise ValueError("Etiquetas de actividad distintas a las contrastadas")
    refs = [nodo.attrib["ref"] for nodo in via.findall("nd")]
    if len(refs) < 100 or len(refs) != len(set(refs)):
        raise ValueError("Secuencia de nodos incompleta o repetida")
    if (refs[0], refs[-1]) != ("1323665115", "1369911783"):
        raise ValueError("Los extremos OSM cambiaron; revisar antes de procesar")
    nodos = {nodo.attrib["id"]: nodo for nodo in raiz.findall("node")}
    if not set(refs) <= nodos.keys():
        raise ValueError("Faltan coordenadas de nodos en el extracto completo")
    for ref in refs:
        lat = float(nodos[ref].attrib["lat"])
        lon = float(nodos[ref].attrib["lon"])
        if not (-0.30 < lat < -0.26 and -78.45 < lon < -78.42):
            raise ValueError("Coordenada fuera de la zona esperada")
    return len(refs)


def main() -> None:
    if SALIDA.exists():
        raise FileExistsError(f"Ya existe una fuente para esta candidata: {SALIDA}")
    solicitud = Request(URL, headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"})
    with urlopen(solicitud, timeout=60) as respuesta:
        contenido = respuesta.read()
    total_nodos = validar(contenido)
    SALIDA.write_bytes(contenido)
    print(f"Fuente conservada: {SALIDA.name}; {total_nodos} nodos")
    print(f"SHA-256: {sha256(contenido).hexdigest().upper()}")


if __name__ == "__main__":
    main()
