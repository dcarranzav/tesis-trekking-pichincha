"""Archiva un recorte OSM acotado del sendero tarabita - Cascada Colibríes/Guarumos (Mindo) sin sobrescribirlo."""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "02_datos_originales/trazados/candidato_guarumos_colibries_mindo_osm_2026-10-22.osm"
URL = "https://api.openstreetmap.org/api/0.6/map?bbox=-78.768,-0.087,-78.757,-0.077"
ESTACION = "352972925"
DESTINOS = {"4891275326": "Cascada Colibries", "3047618576": "Cascada Guarumos"}
VIAS_ESPERADAS = {"964152743", "196510810", "497709953", "301136576", "505208308", "193975746"}


def main() -> None:
    if SALIDA.exists():
        raise FileExistsError(f"Original ya archivado: {SALIDA}")
    solicitud = Request(URL, headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"})
    with urlopen(solicitud, timeout=120) as respuesta:
        contenido = respuesta.read()
    raiz = ET.fromstring(contenido)
    nodos = {n.attrib["id"]: n for n in raiz.findall("node")}
    vias = {via.attrib["id"]: via for via in raiz.findall("way")}
    if ESTACION not in nodos or not set(DESTINOS).issubset(nodos) or not VIAS_ESPERADAS.issubset(vias):
        raise ValueError("El recorte no contiene la estación, las cascadas y las vías esperadas")
    for nodo, nombre in DESTINOS.items():
        etiquetas = {t.attrib["k"]: t.attrib["v"] for t in nodos[nodo].findall("tag")}
        if etiquetas.get("name") != nombre:
            raise ValueError(f"El nodo {nodo} no coincide con {nombre}")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("xb") as archivo:
        archivo.write(contenido)
    print(f"Archivado: {SALIDA.name}; bytes={len(contenido)}; SHA-256={sha256(contenido).hexdigest().upper()}")


if __name__ == "__main__":
    main()
