"""Archiva un recorte OSM acotado de la cascada Guagrapamba sin sobrescribirlo."""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "02_datos_originales/trazados/candidato_guagrapamba_osm_2026-10-21.osm"
URL = "https://api.openstreetmap.org/api/0.6/map?bbox=-78.603,-0.094,-78.583,-0.071"
DESTINO = "8146768136"
VIAS_ESPERADAS = {"1075564180", "1206487315", "1206487316", "1206487459"}


def main() -> None:
    if SALIDA.exists():
        raise FileExistsError(f"Original ya archivado: {SALIDA}")
    solicitud = Request(URL, headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"})
    with urlopen(solicitud, timeout=120) as respuesta:
        contenido = respuesta.read()
    raiz = ET.fromstring(contenido)
    nodos = {n.attrib["id"]: n for n in raiz.findall("node")}
    vias = {via.attrib["id"]: via for via in raiz.findall("way")}
    if DESTINO not in nodos or not VIAS_ESPERADAS.issubset(vias):
        raise ValueError("El recorte no contiene el destino y los cuatro tramos esperados")
    etiquetas = {t.attrib["k"]: t.attrib["v"] for t in nodos[DESTINO].findall("tag")}
    if etiquetas.get("name") != "Cascada Guagrapamba" or etiquetas.get("waterway") != "waterfall":
        raise ValueError("El nodo destino no coincide con Cascada Guagrapamba")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("xb") as archivo:
        archivo.write(contenido)
    print(f"Archivado: {SALIDA.name}; bytes={len(contenido)}; SHA-256={sha256(contenido).hexdigest().upper()}")


if __name__ == "__main__":
    main()
