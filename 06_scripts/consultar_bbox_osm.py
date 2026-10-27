"""Lista vías peatonales nombradas desde un recorte pequeño de la API OSM."""

from argparse import ArgumentParser
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen


ZONAS = {
    "pululahua": (-78.53, -0.01, -78.46, 0.07),
    "maquipucuna": (-78.68, 0.08, -78.60, 0.16),
    "yanacocha": (-78.64, -0.15, -78.56, -0.07),
    "nono": (-78.63, -0.12, -78.54, -0.03),
    "pasochoa": (-78.53, -0.48, -78.46, -0.40),
    "mindo": (-78.82, -0.10, -78.73, -0.01),
    "la_mica": (-78.25, -0.565, -78.19, -0.515),
    "pahuma": (-78.66, -0.005, -78.60, 0.045),
    "santa_lucia": (-78.66, 0.08, -78.57, 0.16),
    "mashpi": (-78.93, 0.10, -78.82, 0.22),
    "yunguilla": (-78.61, -0.06, -78.51, 0.04),
    "jerusalem": (-78.40, -0.035, -78.32, 0.035),
    "cayambe_refugio": (-78.04, -0.025, -77.95, 0.065),
}


def validar_bbox(bbox: tuple[float, float, float, float]) -> None:
    oeste, sur, este, norte = bbox
    if not (-180 <= oeste < este <= 180 and -90 <= sur < norte <= 90):
        raise ValueError("bbox inválida: se espera oeste,sur,este,norte")
    if (este - oeste) * (norte - sur) > 0.25:
        raise ValueError("bbox demasiado grande para la API OSM; divida la zona")


def cargar_bbox(bbox: tuple[float, float, float, float]) -> ET.Element:
    validar_bbox(bbox)
    oeste, sur, este, norte = bbox
    bbox = f"{oeste},{sur},{este},{norte}"
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={bbox}"
    solicitud = Request(
        url,
        headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"},
    )
    with urlopen(solicitud, timeout=240) as respuesta:
        return ET.parse(respuesta).getroot()


def inspeccionar(raiz: ET.Element, incluir_sin_nombre: bool = False) -> list[dict]:

    filas = []
    for via in raiz.findall("way"):
        etiquetas = {
            etiqueta.attrib["k"]: etiqueta.attrib["v"]
            for etiqueta in via.findall("tag")
        }
        if etiquetas.get("highway") not in {"path", "footway", "track"}:
            continue
        if not etiquetas.get("name") and not incluir_sin_nombre:
            continue
        filas.append(
            {
                "id": via.attrib["id"],
                "nombre": etiquetas.get("name", ""),
                "highway": etiquetas.get("highway", ""),
                "sac_scale": etiquetas.get("sac_scale", ""),
                "surface": etiquetas.get("surface", ""),
                "nodos": len(via.findall("nd")),
            }
        )
    return sorted(filas, key=lambda fila: (fila["nombre"], int(fila["id"])))


def consultar(zona: str, incluir_sin_nombre: bool = False) -> list[dict]:
    """Compatibilidad con las consultas por zona usadas anteriormente."""
    return inspeccionar(cargar_bbox(ZONAS[zona]), incluir_sin_nombre)


def main() -> None:
    parser = ArgumentParser()
    origen = parser.add_mutually_exclusive_group(required=True)
    origen.add_argument("--zona", choices=sorted(ZONAS))
    origen.add_argument(
        "--bbox", nargs=4, type=float, metavar=("OESTE", "SUR", "ESTE", "NORTE"),
        help="Recorte pequeño en longitud/latitud; solo consulta, no guarda datos.",
    )
    origen.add_argument(
        "--archivo", type=Path,
        help="Inspecciona un XML OSM local sin conexión ni modificarlo.",
    )
    parser.add_argument(
        "--todos",
        action="store_true",
        help="Incluye vías peatonales sin nombre para auditoría topológica.",
    )
    argumentos = parser.parse_args()
    if argumentos.archivo:
        raiz = ET.parse(argumentos.archivo).getroot()
    else:
        raiz = cargar_bbox(tuple(argumentos.bbox) if argumentos.bbox else ZONAS[argumentos.zona])
    filas = inspeccionar(raiz, argumentos.todos)
    columnas = ["id", "nombre", "highway", "sac_scale", "surface", "nodos"]
    print("\t".join(columnas))
    for fila in filas:
        print("\t".join(str(fila[columna]) for columna in columnas))
    print(f"Elementos encontrados: {len(filas)}")


if __name__ == "__main__":
    main()
