"""Descarga reproducible de las vías OSM del tercer lote en Mindo."""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen


FECHA = "2026-10-09"
VIAS = {
    "acceso_hermit": ("1497391421", f"MINDO_hermit_acceso_osm_{FECHA}.osm"),
    "R015": ("1497391422", f"R015_hermit_cascada_corazon_osm_{FECHA}.osm"),
    "R016": ("1497391425", f"R016_hermit_mirador_osm_{FECHA}.osm"),
    "R017": ("299595681", f"R017_yellow_house_trail_osm_{FECHA}.osm"),
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
    for referencia, (id_via, nombre_archivo) in VIAS.items():
        url = f"https://api.openstreetmap.org/api/0.6/way/{id_via}/full"
        solicitud = Request(url, headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"})
        with urlopen(solicitud, timeout=120) as respuesta:
            contenido = respuesta.read()
        assert contenido.startswith(b"<?xml")
        archivo = carpeta / nombre_archivo
        archivo.write_bytes(contenido)
        print(
            f"{referencia}\tvia={id_via}\tarchivo={archivo.name}\t"
            f"bytes={len(contenido)}\tsha256={sha256(contenido).hexdigest().upper()}"
        )


if __name__ == "__main__":
    main()
