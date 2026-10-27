"""Descarga reproducible del Sendero de la Cascada de Maquipucuna."""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen


FECHA = "2026-10-10"
ID_RUTA = "R018"
ID_VIA = "801959483"
NOMBRE_ARCHIVO = f"R018_maquipucuna_cascada_osm_{FECHA}.osm"


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def main() -> None:
    carpeta = localizar_proyecto() / "02_datos_originales" / "trazados"
    carpeta.mkdir(parents=True, exist_ok=True)
    url = f"https://api.openstreetmap.org/api/0.6/way/{ID_VIA}/full"
    solicitud = Request(
        url,
        headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"},
    )
    with urlopen(solicitud, timeout=120) as respuesta:
        contenido = respuesta.read()
    assert contenido.startswith(b"<?xml")
    archivo = carpeta / NOMBRE_ARCHIVO
    archivo.write_bytes(contenido)
    resumen = sha256(contenido).hexdigest().upper()
    print(
        f"{ID_RUTA}\tvia={ID_VIA}\tarchivo={archivo.name}\t"
        f"bytes={len(contenido)}\tsha256={resumen}"
    )


if __name__ == "__main__":
    main()
