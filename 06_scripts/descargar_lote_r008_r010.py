"""Descarga de forma reproducible las vías OSM del primer lote de ampliación."""

from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen


FECHA = "2026-10-07"
VIAS = {
    "R008": {
        "id_via": "1057988138",
        "archivo": f"R008_pondona_ascenso_osm_{FECHA}.osm",
    },
    "R009": {
        "id_via": "1329296867",
        "archivo": f"R009_maquipucuna_principal_osm_{FECHA}.osm",
    },
    "R010": {
        "id_via": "1329292949",
        "archivo": f"R010_maquipucuna_tranquilo_osm_{FECHA}.osm",
    },
}


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def main() -> None:
    proyecto = localizar_proyecto()
    carpeta = proyecto / "02_datos_originales" / "trazados"
    carpeta.mkdir(parents=True, exist_ok=True)

    for id_ruta, configuracion in VIAS.items():
        url = (
            "https://api.openstreetmap.org/api/0.6/way/"
            f"{configuracion['id_via']}/full"
        )
        solicitud = Request(
            url,
            headers={"User-Agent": "tesis-trekking-pichincha/1.0 academic-use"},
        )
        with urlopen(solicitud, timeout=120) as respuesta:
            contenido = respuesta.read()
        assert contenido.startswith(b"<?xml")

        archivo = carpeta / configuracion["archivo"]
        archivo.write_bytes(contenido)
        resumen = sha256(contenido).hexdigest().upper()
        print(
            f"{id_ruta}\tvia={configuracion['id_via']}\t"
            f"archivo={archivo.name}\tbytes={len(contenido)}\tsha256={resumen}"
        )


if __name__ == "__main__":
    main()
