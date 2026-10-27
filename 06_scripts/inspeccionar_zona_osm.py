"""Inspecciona una zona pequeña de OSM (radio alrededor de un punto) y archiva la respuesta original.

Lista las vías peatonales/senderos con sus etiquetas y los puntos de interés nombrados. Sirve para decidir
si una candidata tiene recorrido completo; no incorpora rutas. Fuente: OpenStreetMap contributors, ODbL.
"""
from __future__ import annotations

import json
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = "https://overpass.kumi.systems/api/interpreter"
VIAS = "path|footway|track|steps|bridleway|pedestrian|unclassified|service|tertiary|residential|living_street"


def consulta(lat: float, lon: float, radio: int) -> str:
    c = f"(around:{radio},{lat},{lon})"
    return (
        f'[out:json][timeout:90];(way["highway"~"^({VIAS})$"]{c};'
        f'nwr["natural"~"^(peak|volcano|saddle|hill)$"]{c};nwr["tourism"~"^(viewpoint|attraction|alpine_hut|wilderness_hut)$"]{c};'
        f'nwr["name"]["historic"]{c};nwr["boundary"~"protected_area|national_park"]{c};);out tags geom qt;'
    )


def resumen(datos: dict) -> list[str]:
    lineas = []
    for e in datos.get("elements", []):
        t = e.get("tags", {})
        if e["type"] == "way":
            g = e.get("geometry", [])
            lineas.append(
                f"way {e['id']} {t.get('highway','')} name={t.get('name','')!r} sac={t.get('sac_scale','')} "
                f"foot={t.get('foot','')} access={t.get('access','')} surface={t.get('surface','')} nodos={len(e.get('nodes', []))} "
                f"ini={e['nodes'][0] if e.get('nodes') else ''} fin={e['nodes'][-1] if e.get('nodes') else ''}"
            )
        else:
            lineas.append(f"{e['type']} {e['id']} name={t.get('name','')!r} " + json.dumps({k: v for k, v in t.items() if k != 'name'}, ensure_ascii=False))
    return lineas


def descargar(lat: float, lon: float, radio: int) -> dict:
    cuerpo = urlencode({"data": consulta(lat, lon, radio)}).encode()
    for intento in range(3):
        try:
            with urlopen(Request(ENDPOINT, data=cuerpo, headers={"User-Agent": "tesis-trekking-pichincha/1.0"}), timeout=120) as r:
                return json.load(r)
        except (HTTPError, URLError, TimeoutError):
            time.sleep(20 * (intento + 1))
    raise RuntimeError(f"Sin respuesta en {lat},{lon}")


def resumen_xml(texto: bytes) -> list[str]:
    """Resumen de una respuesta de la API de OSM (`/map`): vías peatonales y puntos nombrados."""
    import xml.etree.ElementTree as ET
    raiz = ET.fromstring(texto)
    lineas = []
    for v in raiz.findall("way"):
        t = {x.get("k"): x.get("v") for x in v.findall("tag")}
        nodos = [n.get("ref") for n in v.findall("nd")]
        if t.get("highway") in set(VIAS.split("|")):
            lineas.append(
                f"way {v.get('id')} {t.get('highway')} name={t.get('name', '')!r} sac={t.get('sac_scale', '')} "
                f"foot={t.get('foot', '')} access={t.get('access', '')} surface={t.get('surface', '')} nodos={len(nodos)} "
                f"ini={nodos[0]} fin={nodos[-1]}"
            )
    for n in raiz.findall("node"):
        t = {x.get("k"): x.get("v") for x in n.findall("tag")}
        if t.get("name") and (t.get("natural") or t.get("tourism") or t.get("historic") or t.get("waterway")):
            lineas.append(f"node {n.get('id')} name={t['name']!r} " + json.dumps({k: v for k, v in t.items() if k != 'name'}, ensure_ascii=False))
    return lineas


def descargar_api(lat: float, lon: float, semilado: float) -> bytes:
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={lon - semilado},{lat - semilado},{lon + semilado},{lat + semilado}"
    for intento in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "tesis-trekking-pichincha/1.0 (verificacion academica)"}), timeout=120) as r:
                return r.read()
        except (HTTPError, URLError, TimeoutError):
            time.sleep(20 * (intento + 1))
    raise RuntimeError(f"Sin respuesta de la API en {lat},{lon}")


def main() -> None:
    p = ArgumentParser()
    p.add_argument("nombre")
    p.add_argument("lat", type=float)
    p.add_argument("lon", type=float)
    p.add_argument("--radio", type=int, default=1500)
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--api", action="store_true", help="Usa la API de mapa de OSM (semilado = radio/111000 grados)")
    a = p.parse_args()
    a.carpeta.mkdir(parents=True, exist_ok=True)
    if a.api:
        xml = descargar_api(a.lat, a.lon, a.radio / 111000)
        (a.carpeta / f"{a.nombre}_osm_api_{time.strftime('%Y-%m-%d')}.xml").write_bytes(xml)
        (a.carpeta / f"{a.nombre}_resumen.txt").write_text("\n".join(resumen_xml(xml)), encoding="utf-8")
        print(f"{a.nombre}: archivado", flush=True)
        return
    datos = descargar(a.lat, a.lon, a.radio)
    (a.carpeta / f"{a.nombre}_overpass_{datos.get('osm3s', {}).get('timestamp_osm_base', 'sin_fecha')[:10]}.json").write_text(
        json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    (a.carpeta / f"{a.nombre}_resumen.txt").write_text("\n".join(resumen(datos)), encoding="utf-8")
    print(f"{a.nombre}: {len(datos.get('elements', []))} elementos", flush=True)


if __name__ == "__main__":
    sys.exit(main())
