"""Busca recorridos candidatos en un XML OSM archivado, sin unir nada por cercanía.

Para cada punto de interés nombrado que sea un nodo de una vía peatonal (extremo o vértice), calcula el camino
más corto por nodos compartidos desde un empalme con una vía vehicular y una segunda alternativa que evite las
aristas de la primera. Solo descubre candidatas: la validación I01–I10 sigue siendo manual.
Fuente de datos: OpenStreetMap contributors, ODbL.
"""
from __future__ import annotations

import heapq
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PEATONALES = {"path", "footway", "steps", "track", "bridleway", "pedestrian"}
VEHICULARES = {"residential", "unclassified", "service", "tertiary", "secondary", "primary", "living_street", "trunk"}
INTERES = ("natural", "tourism", "waterway", "historic", "man_made")  # o bien extremo nombrado de una vía peatonal


def _m(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot((a[0] - b[0]) * 111000, (a[1] - b[1]) * 111000 * math.cos(math.radians(a[0])))


def cargar(ruta: Path):
    raiz = ET.parse(ruta).getroot()
    nodos = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in raiz.findall("node")}
    etq = {n.get("id"): {t.get("k"): t.get("v") for t in n.findall("tag")} for n in raiz.findall("node")}
    vias = {}
    for w in raiz.findall("way"):
        t = {x.get("k"): x.get("v") for x in w.findall("tag")}
        if t.get("highway"):
            vias[w.get("id")] = (t, [n.get("ref") for n in w.findall("nd")], w.get("timestamp", ""), w.get("version", ""))
    return nodos, etq, vias


def grafo(nodos, vias):
    g: dict[str, list[tuple[str, float, str]]] = {}
    contactos: set[str] = set()
    vehicular: set[str] = set()
    for wid, (t, ids, _, _) in vias.items():
        if t["highway"] in VEHICULARES:
            vehicular.update(ids)
        if t["highway"] in PEATONALES and t.get("access") != "no" and t.get("foot") != "no":
            for a, b in zip(ids, ids[1:]):
                if a in nodos and b in nodos:
                    d = _m(nodos[a], nodos[b])
                    g.setdefault(a, []).append((b, d, wid))
                    g.setdefault(b, []).append((a, d, wid))
    contactos = vehicular & set(g)
    return g, contactos


def camino(g, origenes, destino, prohibidas=frozenset()):
    dist = {o: 0.0 for o in origenes}
    prev: dict[str, tuple[str, str]] = {}
    cola = [(0.0, o) for o in origenes]
    heapq.heapify(cola)
    while cola:
        c, u = heapq.heappop(cola)
        if u == destino:
            break
        if c > dist.get(u, 1e18):
            continue
        for v, d, wid in g.get(u, []):
            if frozenset((u, v)) in prohibidas:
                continue
            if c + d < dist.get(v, 1e18):
                dist[v] = c + d
                prev[v] = (u, wid)
                heapq.heappush(cola, (c + d, v))
    if destino not in dist:
        return None
    nodos_c, vias_c = [destino], []
    while nodos_c[-1] in prev:
        u, wid = prev[nodos_c[-1]]
        vias_c.append(wid)
        nodos_c.append(u)
    return round(dist[destino]), nodos_c[::-1], vias_c[::-1]


def candidatas(ruta: Path) -> list[dict]:
    nodos, etq, vias = cargar(ruta)
    g, contactos = grafo(nodos, vias)
    filas = []
    extremos = {i for t, ids, _, _ in vias.values() if t["highway"] in PEATONALES for i in (ids[0], ids[-1])}
    for nid, t in etq.items():
        if not t.get("name") or nid not in g or not (any(k in t for k in INTERES) or nid in extremos):
            continue
        c1 = camino(g, contactos, nid)
        # Un POI en el mismo nodo de empalme produce un camino de longitud
        # cero, sin ninguna vía peatonal. No es una ruta candidata.
        if not c1 or not c1[2]:
            continue
        aristas = {frozenset(par) for par in zip(c1[1], c1[1][1:])}
        c2 = camino(g, contactos, nid, aristas)
        usadas = {k: vias[w][0].get("highway") for w in c1[2] for k in [w]}
        sac = {vias[w][0].get("sac_scale", "") for w in c1[2]} - {""}
        filas.append({
            "nodo": nid, "nombre": t["name"], "tipo": next((f"{k}={t[k]}" for k in INTERES if k in t), "extremo_nombrado"),
            "inicio": c1[1][0], "longitud_m": c1[0], "vias": "|".join(dict.fromkeys(c1[2])),
            "highway": "|".join(sorted(set(usadas.values()))), "sac_scale": "|".join(sorted(sac)),
            "alternativa_m": c2[0] if c2 else "", "alt_vias": "|".join(dict.fromkeys(c2[2])) if c2 else "",
            "fecha_vias": max(vias[w][2] for w in c1[2])[:10], "versiones": "|".join(vias[w][3] for w in dict.fromkeys(c1[2])),
        })
    return sorted(filas, key=lambda f: -f["longitud_m"])


def main() -> None:
    for archivo in sys.argv[1:]:
        print(f"== {archivo}")
        for f in candidatas(Path(archivo)):
            print(" ", f)


if __name__ == "__main__":
    main()
