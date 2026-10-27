"""Consulta exploratoria reproducible de senderos nombrados en OpenStreetMap."""

from argparse import ArgumentParser
import json
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ZONAS = {
    "pululahua": (0.040, -78.490, 9000),
    "yanacocha": (-0.115, -78.590, 5000),
    "choco_andino": (0.020, -78.650, 12000),
    "pasochoa": (-0.440, -78.490, 8000),
}


def construir_consulta(latitud: float, longitud: float, radio_m: int) -> str:
    return f"""
[out:json][timeout:180];
(
  way(around:{radio_m},{latitud},{longitud})
    ["highway"~"^(path|footway|track)$"]
    ["name"];
);
out tags center;
""".strip()


def consultar(zona: str, endpoint: str) -> list[dict]:
    latitud, longitud, radio_m = ZONAS[zona]
    cuerpo = urlencode(
        {"data": construir_consulta(latitud, longitud, radio_m)}
    ).encode("utf-8")
    solicitud = Request(
        endpoint,
        data=cuerpo,
        headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"},
    )
    try:
        with urlopen(solicitud, timeout=240) as respuesta:
            datos = json.load(respuesta)
    except HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Overpass respondió HTTP {error.code}: {detalle[:1000]}"
        ) from error

    filas = []
    for elemento in datos["elements"]:
        etiquetas = elemento.get("tags", {})
        filas.append(
            {
                "zona": zona,
                "tipo": elemento["type"],
                "id": elemento["id"],
                "nombre": etiquetas.get("name", ""),
                "highway": etiquetas.get("highway", ""),
                "route": etiquetas.get("route", ""),
                "sac_scale": etiquetas.get("sac_scale", ""),
            }
        )
    return sorted(filas, key=lambda fila: (fila["nombre"], fila["tipo"], fila["id"]))


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--zona", choices=sorted(ZONAS), required=True)
    parser.add_argument(
        "--endpoint",
        default="https://overpass.private.coffee/api/interpreter",
    )
    argumentos = parser.parse_args()

    filas = consultar(argumentos.zona, argumentos.endpoint)
    print("zona\ttipo\tid\tnombre\thighway\troute\tsac_scale")
    for fila in filas:
        print("\t".join(str(fila[columna]) for columna in fila))
    print(f"Elementos encontrados: {len(filas)}")


if __name__ == "__main__":
    main()
