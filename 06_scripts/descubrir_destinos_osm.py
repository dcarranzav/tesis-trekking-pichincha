"""Descubre candidatas de ruta: vías peatonales de OSM cuyo extremo toca un destino etiquetado.

Solo LEE OpenStreetMap mediante Overpass o su API (recortes pequeños) y escribe candidatas en la
carpeta indicada. No modifica inventario, trazados ni dataset. Un candidato listado aquí NO es una ruta
incorporada: todavía hay que archivar el XML original, comprobar continuidad, destino, licencia y
carácter no técnico (criterios I01–I10 de `01_documentacion/criterios_seleccion_rutas.md`).
"""

from __future__ import annotations

import csv
import math
import sys
import time
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

VIAS = {"path", "footway", "track", "steps", "bridleway"}
# Etiquetas que identifican un destino turístico verificable en el nodo extremo.
DESTINOS = (
    ("waterway", {"waterfall"}), ("natural", {"peak", "volcano", "saddle", "cave_entrance", "spring", "hot_spring"}),
    ("tourism", {"viewpoint", "attraction", "camp_site", "alpine_hut", "wilderness_hut"}),
    ("amenity", {"shelter"}), ("natural", {"water"}), ("man_made", {"cross", "tower"}),
    ("historic", {"memorial", "ruins", "archaeological_site"}),
)
USER_AGENT = "tesis-trekking-pichincha/1.0 academic-use (descubrimiento de candidatas)"


def distancia_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat0 = math.radians((a[0] + b[0]) / 2)
    return math.hypot((b[1] - a[1]) * 111320 * math.cos(lat0), (b[0] - a[0]) * 110574)


def teselas(oeste: float, sur: float, este: float, norte: float, paso: float):
    y = sur
    while y < norte - 1e-9:
        x = oeste
        while x < este - 1e-9:
            yield (round(x, 4), round(y, 4), round(min(x + paso, este), 4), round(min(y + paso, norte), 4))
            x += paso
        y += paso


def descargar(bbox: tuple[float, float, float, float], espera: float = 1.0) -> ET.Element | None:
    url = "https://api.openstreetmap.org/api/0.6/map?bbox=" + ",".join(str(v) for v in bbox)
    for intento in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=240) as r:
                raiz = ET.parse(r).getroot()
            time.sleep(espera)
            return raiz
        except HTTPError as error:
            if error.code == 400:  # demasiados nodos: el llamador subdivide
                return None
            if error.code in (429, 502, 503, 504):
                time.sleep(20 * (intento + 1))
                continue
            raise
        except (URLError, TimeoutError, ET.ParseError):
            time.sleep(10 * (intento + 1))
    raise RuntimeError(f"No se pudo descargar {bbox}")


def etiquetas(elemento: ET.Element) -> dict[str, str]:
    return {t.attrib["k"]: t.attrib["v"] for t in elemento.findall("tag")}


def es_destino(tags: dict[str, str]) -> str:
    for clave, valores in DESTINOS:
        if tags.get(clave) in valores:
            return f"{clave}={tags[clave]}"
    return ""


def candidatas(raiz: ET.Element, tesela: str) -> list[dict]:
    nodos = {}
    for n in raiz.findall("node"):
        nodos[n.attrib["id"]] = (float(n.attrib["lat"]), float(n.attrib["lon"]), etiquetas(n))
    vias = []
    for w in raiz.findall("way"):
        t = etiquetas(w)
        if t.get("highway") not in VIAS:
            continue
        refs = [nd.attrib["ref"] for nd in w.findall("nd")]
        if len(refs) < 2 or any(r not in nodos for r in refs):
            continue
        vias.append((w.attrib["id"], t, refs))
    por_extremo: dict[str, list[str]] = {}
    for id_via, _, refs in vias:
        for extremo in (refs[0], refs[-1]):
            por_extremo.setdefault(extremo, []).append(id_via)
    filas = []
    for id_via, t, refs in vias:
        coords = [nodos[r][:2] for r in refs]
        largo = sum(distancia_m(coords[i], coords[i + 1]) for i in range(len(coords) - 1))
        for lado, extremo in (("final", refs[-1]), ("inicio", refs[0])):
            poi = es_destino(nodos[extremo][2])
            if not poi:
                continue
            filas.append(
                {
                    "tesela": tesela, "id_via": id_via, "nombre_via": t.get("name", ""), "highway": t["highway"],
                    "sac_scale": t.get("sac_scale", ""), "surface": t.get("surface", ""), "foot": t.get("foot", ""),
                    "access": t.get("access", ""), "nodos": len(refs), "longitud_m": round(largo),
                    "extremo": lado, "id_nodo_destino": extremo, "tipo_destino": poi,
                    "nombre_destino": nodos[extremo][2].get("name", ""),
                    "lat_destino": nodos[extremo][0], "lon_destino": nodos[extremo][1],
                    "otras_vias_mismo_destino": "|".join(v for v in por_extremo[extremo] if v != id_via),
                }
            )
    return filas


ENDPOINT_OVERPASS = "https://overpass.kumi.systems/api/interpreter"
TIEMPO_OVERPASS = 90
CAMPOS = (
    "tesela", "id_via", "nombre_via", "highway", "sac_scale", "surface", "foot", "access",
    "nodos", "longitud_m", "extremo", "id_nodo_destino", "tipo_destino", "nombre_destino",
    "lat_destino", "lon_destino", "otras_vias_mismo_destino", "fecha_datos_osm",
)


def consulta_overpass(bbox: tuple[float, float, float, float]) -> str:
    oeste, sur, este, norte = bbox
    c = f"({sur},{oeste},{norte},{este})"
    return (
        f"[out:json][timeout:{TIEMPO_OVERPASS}];("
        f'node["waterway"="waterfall"]{c};node["natural"~"^(peak|volcano|saddle|cave_entrance|hot_spring)$"]{c};'
        f'node["tourism"~"^(viewpoint|alpine_hut|wilderness_hut|attraction)$"]{c};node["man_made"="cross"]{c};'
        ")->.p;way(bn.p)[\"highway\"~\"^(path|footway|track|steps|bridleway)$\"];out body geom;.p out body;"
    )


def candidatas_overpass(datos: dict, tesela: str) -> list[dict]:
    """Igual que `candidatas`, pero con la respuesta JSON de Overpass (vías que tocan un destino)."""
    pois = {
        str(e["id"]): e for e in datos.get("elements", []) if e["type"] == "node" and es_destino(e.get("tags", {}))
    }
    fecha = datos.get("osm3s", {}).get("timestamp_osm_base", "")
    vias = [e for e in datos.get("elements", []) if e["type"] == "way" and e.get("geometry")]
    por_extremo: dict[str, list[str]] = {}
    for v in vias:
        for extremo in (str(v["nodes"][0]), str(v["nodes"][-1])):
            por_extremo.setdefault(extremo, []).append(str(v["id"]))
    filas = []
    for v in vias:
        coords = [(g["lat"], g["lon"]) for g in v["geometry"]]
        largo = sum(distancia_m(coords[i], coords[i + 1]) for i in range(len(coords) - 1))
        t = v.get("tags", {})
        for lado, extremo in (("final", str(v["nodes"][-1])), ("inicio", str(v["nodes"][0]))):
            poi = pois.get(extremo)
            if not poi:
                continue
            tp = poi.get("tags", {})
            filas.append(
                {
                    "tesela": tesela, "id_via": str(v["id"]), "nombre_via": t.get("name", ""), "highway": t.get("highway", ""),
                    "sac_scale": t.get("sac_scale", ""), "surface": t.get("surface", ""), "foot": t.get("foot", ""),
                    "access": t.get("access", ""), "nodos": len(v["nodes"]), "longitud_m": round(largo),
                    "extremo": lado, "id_nodo_destino": extremo, "tipo_destino": es_destino(tp),
                    "nombre_destino": tp.get("name", ""), "lat_destino": poi["lat"], "lon_destino": poi["lon"],
                    "otras_vias_mismo_destino": "|".join(x for x in por_extremo[extremo] if x != str(v["id"])),
                    "fecha_datos_osm": fecha,
                }
            )
    return filas


def descargar_overpass(bbox, endpoint: str = ENDPOINT_OVERPASS) -> dict:
    import json
    from urllib.parse import urlencode
    cuerpo = urlencode({"data": consulta_overpass(bbox)}).encode("utf-8")
    for intento in range(2):
        try:
            with urlopen(Request(endpoint, data=cuerpo, headers={"User-Agent": USER_AGENT}), timeout=TIEMPO_OVERPASS + 20) as r:
                return json.load(r)
        except HTTPError as error:
            if error.code in (429, 502, 503, 504):
                time.sleep(30 * (intento + 1))
                continue
            raise
        except (URLError, TimeoutError):
            time.sleep(15 * (intento + 1))
    raise RuntimeError(f"No se pudo consultar Overpass para {bbox}")


def clave_fila(fila: dict) -> tuple[str, str, str]:
    return (fila["id_via"], fila["extremo"], fila["id_nodo_destino"])


def explorar_incremental(bboxes, salida: Path, fuente: str, registro=print, limite_teselas: int | None = None) -> tuple[int, int]:
    """Guarda cada tesela terminada; una ejecución interrumpida se puede reanudar sin duplicar filas."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    progreso = salida.with_name(salida.stem + ".teselas.csv")
    completadas: set[str] = set()
    if progreso.exists():
        with progreso.open(encoding="utf-8-sig", newline="") as f:
            completadas = {fila["tesela"] for fila in csv.DictReader(f)}
    claves: set[tuple[str, str, str]] = set()
    if salida.exists():
        with salida.open(encoding="utf-8-sig", newline="") as f:
            lector = csv.DictReader(f)
            if lector.fieldnames != list(CAMPOS):
                raise ValueError(f"El encabezado existente no coincide con el formato actual: {salida}")
            claves = {clave_fila(fila) for fila in lector}
    nuevas = 0
    consultadas = 0
    with salida.open("a", encoding="utf-8-sig" if not salida.exists() else "utf-8", newline="") as f_datos, progreso.open(
        "a", encoding="utf-8-sig" if not progreso.exists() else "utf-8", newline=""
    ) as f_progreso:
        escritor = csv.DictWriter(f_datos, fieldnames=CAMPOS)
        avance = csv.DictWriter(f_progreso, fieldnames=("tesela", "filas_nuevas"))
        if f_datos.tell() == 0:
            escritor.writeheader()
            f_datos.flush()
        if f_progreso.tell() == 0:
            avance.writeheader()
            f_progreso.flush()
        for bbox in bboxes:
            etiqueta = ",".join(str(v) for v in bbox)
            if etiqueta in completadas:
                continue
            if limite_teselas is not None and consultadas >= limite_teselas:
                break
            registro(f"Consultando {etiqueta}")
            if fuente == "overpass":
                filas = candidatas_overpass(descargar_overpass(bbox), etiqueta)
            else:
                filas = explorar(bbox, bbox[2] - bbox[0], 2, registro)
            sin_duplicados = []
            for fila in filas:
                clave = clave_fila(fila)
                if clave not in claves:
                    claves.add(clave)
                    sin_duplicados.append(fila)
            escritor.writerows(sin_duplicados)
            f_datos.flush()
            avance.writerow({"tesela": etiqueta, "filas_nuevas": len(sin_duplicados)})
            f_progreso.flush()
            completadas.add(etiqueta)
            consultadas += 1
            nuevas += len(sin_duplicados)
            registro(f"{etiqueta}: {len(sin_duplicados)} candidatas nuevas; guardadas en {salida}")
            if fuente == "overpass":
                time.sleep(2)
    return consultadas, nuevas


def explorar(bbox, paso, profundidad_max, registro) -> list[dict]:
    raiz = descargar(bbox)
    if raiz is None:
        if profundidad_max <= 0:
            registro(f"OMITIDA (demasiado densa): {bbox}")
            return []
        filas = []
        for sub in teselas(*bbox, paso / 2):
            filas += explorar(sub, paso / 2, profundidad_max - 1, registro)
        return filas
    filas = candidatas(raiz, ",".join(str(v) for v in bbox))
    registro(f"{bbox}: {len(filas)} candidatas")
    return filas


def main() -> None:
    p = ArgumentParser()
    p.add_argument("--bbox", nargs=4, type=float, metavar=("OESTE", "SUR", "ESTE", "NORTE"),
                   default=[-79.20, -0.58, -77.85, 0.27])
    p.add_argument("--paso", type=float, default=0.15)
    p.add_argument("--salida", type=Path, required=True)
    p.add_argument("--fuente", choices=["overpass", "api"], default="overpass")
    p.add_argument("--limite-teselas", type=int, help="Número máximo de teselas nuevas en esta ejecución")
    args = p.parse_args()
    if args.paso <= 0 or (args.limite_teselas is not None and args.limite_teselas <= 0):
        p.error("--paso y --limite-teselas deben ser positivos")
    registro = lambda m: print(m, flush=True)  # noqa: E731
    consultadas, nuevas = explorar_incremental(
        teselas(*args.bbox, args.paso), args.salida, args.fuente, registro, args.limite_teselas
    )
    print(f"Teselas nuevas: {consultadas}; candidatas nuevas: {nuevas}; salida: {args.salida}")


if __name__ == "__main__":
    sys.exit(main())
