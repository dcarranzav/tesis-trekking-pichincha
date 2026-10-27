"""Busca por nombre elementos OSM en Pichincha (consulta pequeña a Overpass) y guarda el resultado incremental.

Fuente: OpenStreetMap contributors, ODbL. Solo descubrimiento: no incorpora rutas.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = "https://overpass.kumi.systems/api/interpreter"
BBOX = (-0.58, -79.20, 0.27, -77.85)  # sur, oeste, norte, este
CAMPOS = ("patron", "tipo", "id", "nombre", "lat", "lon", "etiquetas", "fecha_datos_osm")


def consulta(patron: str) -> str:
    s, o, n, e = BBOX
    return f'[out:json][timeout:90];nwr["name"~"{patron}",i]({s},{o},{n},{e});out center tags;'


def buscar(patron: str, endpoint: str = ENDPOINT) -> dict:
    cuerpo = urlencode({"data": consulta(patron)}).encode()
    for intento in range(3):
        try:
            with urlopen(Request(endpoint, data=cuerpo, headers={"User-Agent": "tesis-trekking-pichincha/1.0"}), timeout=120) as r:
                return json.load(r)
        except (HTTPError, URLError, TimeoutError):
            time.sleep(20 * (intento + 1))
    raise RuntimeError(f"Sin respuesta para {patron}")


def filas(patron: str, datos: dict) -> list[dict]:
    fecha = datos.get("osm3s", {}).get("timestamp_osm_base", "")
    out = []
    for e in datos.get("elements", []):
        c = e.get("center") or {"lat": e.get("lat", ""), "lon": e.get("lon", "")}
        out.append({"patron": patron, "tipo": e["type"], "id": e["id"], "nombre": e.get("tags", {}).get("name", ""),
                    "lat": c["lat"], "lon": c["lon"], "etiquetas": json.dumps(e.get("tags", {}), ensure_ascii=False),
                    "fecha_datos_osm": fecha})
    return out


def main() -> None:
    p = ArgumentParser()
    p.add_argument("patrones", nargs="+")
    p.add_argument("--salida", type=Path, required=True)
    a = p.parse_args()
    nuevo = not a.salida.exists()
    with a.salida.open("a", encoding="utf-8-sig" if nuevo else "utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        for patron in a.patrones:
            r = filas(patron, buscar(patron))
            w.writerows(r)
            f.flush()
            print(f"{patron}: {len(r)} elementos", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    sys.exit(main())
