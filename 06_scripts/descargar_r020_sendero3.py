"""Conserva la vía OSM Sendero 3 para la variante Yellow House R020.

No reemplaza originales existentes ni modifica el extracto R017 compartido.
"""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
ID_VIA = "299595680"
SALIDA = RAIZ / "02_datos_originales/trazados/R020_yellow_house_sendero3_osm_2026-10-14.osm"
URL = f"https://api.openstreetmap.org/api/0.6/way/{ID_VIA}/full"


def main() -> None:
    if SALIDA.exists():
        raise FileExistsError(f"El original ya existe: {SALIDA}")
    solicitud = Request(URL, headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"})
    with urlopen(solicitud, timeout=120) as respuesta:
        contenido = respuesta.read()
    raiz = ET.fromstring(contenido)
    via = next((w for w in raiz.findall("way") if w.attrib["id"] == ID_VIA), None)
    assert via is not None, "No aparece la vía OSM esperada"
    etiquetas = {t.attrib["k"]: t.attrib["v"] for t in via.findall("tag")}
    assert etiquetas.get("name") == "Sendero 3"
    assert etiquetas.get("highway") == "footway"
    assert etiquetas.get("sac_scale") == "mountain_hiking"
    SALIDA.write_bytes(contenido)
    print(f"{SALIDA.name}\tsha256={sha256(contenido).hexdigest().upper()}")


if __name__ == "__main__":
    main()
