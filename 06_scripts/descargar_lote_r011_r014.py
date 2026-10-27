"""Descarga reproducible de cuatro senderos de la Reserva Yanacocha."""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen


FECHA = "2026-10-09"
VIAS = {
    "R011": ("470057044", f"R011_yanacocha_masked_trogon_osm_{FECHA}.osm"),
    "R012": ("470057046", f"R012_yanacocha_andean_snipe_osm_{FECHA}.osm"),
    "R013": ("470057048", f"R013_yanacocha_oso_anteojos_osm_{FECHA}.osm"),
    "R014": ("723159928", f"R014_yanacocha_trocha_inca_osm_{FECHA}.osm"),
}


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def main() -> None:
    carpeta = localizar_proyecto() / "02_datos_originales" / "trazados"
    carpeta.mkdir(parents=True, exist_ok=True)
    for id_ruta, (id_via, nombre_archivo) in VIAS.items():
        url = f"https://api.openstreetmap.org/api/0.6/way/{id_via}/full"
        solicitud = Request(
            url,
            headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"},
        )
        with urlopen(solicitud, timeout=120) as respuesta:
            contenido = respuesta.read()
        assert contenido.startswith(b"<?xml")
        archivo = carpeta / nombre_archivo
        archivo.write_bytes(contenido)
        resumen = sha256(contenido).hexdigest().upper()
        print(
            f"{id_ruta}\tvia={id_via}\tarchivo={archivo.name}\t"
            f"bytes={len(contenido)}\tsha256={resumen}"
        )


if __name__ == "__main__":
    main()
