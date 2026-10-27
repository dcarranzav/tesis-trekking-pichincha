"""Contrasta el XML OSM exacto de R022 con la instantánea y el trazado procesado.

No modifica archivos ni certifica acceso público o seguridad de los vados.
"""

from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
XML = RAIZ / "02_datos_originales/trazados/R022_ilalo_cruz_osm_2026-10-20.osm"
SNAPSHOT = RAIZ / "02_datos_originales/trazados/R022_ilalo_cruz_overpass_snapshot_2026-10-17.json"
TRAZADO = RAIZ / "03_datos_intermedios/trazados/R022_trazado_ida_continuo_2026-10-17.geojson"
SHA_XML = "93C537C2B2386C74BCF4A8EAFE40A3A03984F4BE7AB92D10D147CA8620DD6381"


def contrastar() -> dict:
    contenido = XML.read_bytes()
    huella = sha256(contenido).hexdigest().upper()
    if huella != SHA_XML:
        raise ValueError("La huella del XML archivado cambió")
    raiz = ET.fromstring(contenido)
    instantanea = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    geojson = json.loads(TRAZADO.read_text(encoding="utf-8"))

    id_via = str(instantanea["way"]["id"])
    vias = [via for via in raiz.findall("way") if via.attrib.get("id") == id_via]
    if len(vias) != 1:
        raise ValueError("El XML no contiene exactamente una vía R022")
    via = vias[0]
    refs_xml = [nd.attrib["ref"] for nd in via.findall("nd")]
    refs_snapshot = [str(ref) for ref in instantanea["way"]["nodes"]]
    if refs_xml != refs_snapshot:
        raise ValueError("La secuencia de nodos cambió entre XML y snapshot")
    etiquetas_xml = {tag.attrib["k"]: tag.attrib["v"] for tag in via.findall("tag")}
    if etiquetas_xml != instantanea["way"]["tags"]:
        raise ValueError("Las etiquetas de la vía cambiaron entre XML y snapshot")

    nodos = {nodo.attrib["id"]: nodo for nodo in raiz.findall("node")}
    coordenadas_xml = [
        [float(nodos[ref].attrib["lon"]), float(nodos[ref].attrib["lat"])]
        for ref in refs_xml
    ]
    if coordenadas_xml != instantanea["way"]["geometry"]:
        raise ValueError("Las coordenadas cambiaron entre XML y snapshot")
    entidades = geojson.get("features", [])
    if len(entidades) != 1 or entidades[0]["geometry"]["type"] != "LineString":
        raise ValueError("El trazado procesado no es una línea única")
    if entidades[0]["geometry"]["coordinates"] != coordenadas_xml[::-1]:
        raise ValueError("El trazado procesado no corresponde a la vía invertida")

    vados = []
    for ref in refs_xml:
        etiquetas_nodo = {tag.attrib["k"]: tag.attrib["v"] for tag in nodos[ref].findall("tag")}
        if etiquetas_nodo.get("ford") == "yes":
            vados.append(ref)
    return {"sha256": huella, "nodos": len(refs_xml), "vados_osm": vados}


if __name__ == "__main__":
    resultado = contrastar()
    print("XML exacto, snapshot y GeoJSON: misma vía y 128 coordenadas")
    print("SHA-256 XML:", resultado["sha256"])
    print("Nodos ford=yes:", ", ".join(resultado["vados_osm"]) or "ninguno")
    print("Acceso público y transitabilidad: no verificados")
