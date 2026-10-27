"""Archiva un recorte OSM acotado del Mirador Cerro de la Luz (Puéllaro) sin sobrescribirlo."""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "02_datos_originales/trazados/candidato_cerro_luz_puellaro_osm_2026-10-21.osm"
URL = "https://api.openstreetmap.org/api/0.6/map?bbox=-78.408,0.052,-78.395,0.060"
DESTINO = "11204680653"
VIAS_ESPERADAS = {"1209333234", "1421205624", "1421205625", "877695136", "1421205621"}


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
        raise ValueError("El recorte no contiene el mirador y las vías esperadas")
    etiquetas = {t.attrib["k"]: t.attrib["v"] for t in nodos[DESTINO].findall("tag")}
    if etiquetas.get("name") != "CERRO DE LA LUZ":
        raise ValueError("El nodo destino no coincide con CERRO DE LA LUZ")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("xb") as archivo:
        archivo.write(contenido)
    print(f"Archivado: {SALIDA.name}; bytes={len(contenido)}; SHA-256={sha256(contenido).hexdigest().upper()}")


if __name__ == "__main__":
    main()
