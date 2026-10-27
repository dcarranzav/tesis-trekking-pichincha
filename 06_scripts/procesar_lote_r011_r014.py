"""Construye y valida geometrías de cuatro senderos de Yanacocha."""

from pathlib import Path
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from shapely.geometry import LineString


FECHA = "2026-10-09"
RUTAS = {
    "R011": {
        "nombre": "Sendero Masked Trogon",
        "id_via": "470057044",
        "nombre_osm": "Masked Trogon",
        "original": f"R011_yanacocha_masked_trogon_osm_{FECHA}.osm",
    },
    "R012": {
        "nombre": "Sendero Andean Snipe",
        "id_via": "470057046",
        "nombre_osm": "Andean Snipe Trail",
        "original": f"R012_yanacocha_andean_snipe_osm_{FECHA}.osm",
    },
    "R013": {
        "nombre": "Sendero Oso de Anteojos",
        "id_via": "470057048",
        "nombre_osm": "Oso de Anteojos",
        "original": f"R013_yanacocha_oso_anteojos_osm_{FECHA}.osm",
    },
    "R014": {
        "nombre": "Trocha Inca",
        "id_via": "723159928",
        "nombre_osm": "Trocha Inca",
        "original": f"R014_yanacocha_trocha_inca_osm_{FECHA}.osm",
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
    originales = proyecto / "02_datos_originales" / "trazados"
    intermedios = proyecto / "03_datos_intermedios" / "trazados"
    intermedios.mkdir(parents=True, exist_ok=True)

    for id_ruta, configuracion in RUTAS.items():
        raiz = ET.parse(originales / configuracion["original"]).getroot()
        nodos = {
            nodo.attrib["id"]: (
                float(nodo.attrib["lon"]),
                float(nodo.attrib["lat"]),
            )
            for nodo in raiz.findall("node")
        }
        via = next(
            elemento
            for elemento in raiz.findall("way")
            if elemento.attrib["id"] == configuracion["id_via"]
        )
        referencias = [elemento.attrib["ref"] for elemento in via.findall("nd")]
        etiquetas = {
            elemento.attrib["k"]: elemento.attrib["v"]
            for elemento in via.findall("tag")
        }
        assert etiquetas.get("name") == configuracion["nombre_osm"]
        assert etiquetas.get("highway") == "path"
        assert len(referencias) == len(set(referencias))

        geometria = LineString([nodos[referencia] for referencia in referencias])
        resultado = gpd.GeoDataFrame(
            [
                {
                    "id_ruta": id_ruta,
                    "nombre": configuracion["nombre"],
                    "id_via_osm": configuracion["id_via"],
                    "nombre_osm": etiquetas["name"],
                    "nodo_inicio": referencias[0],
                    "nodo_fin": referencias[-1],
                    "tipo_recorrido": "ida_y_vuelta",
                    "estado": "via_osm_completa_pendiente_revision_extremos",
                    "fecha": FECHA,
                    "geometry": geometria,
                }
            ],
            crs="EPSG:4326",
        )
        distancia_km = float(resultado.to_crs(32717).length.iloc[0] / 1000)
        resultado["distancia_ida_km"] = round(distancia_km, 3)
        salida = intermedios / f"{id_ruta}_trazado_ida_continuo_{FECHA}.geojson"
        resultado.to_file(salida, driver="GeoJSON")

        comprobacion = gpd.read_file(salida)
        assert len(comprobacion) == 1
        assert comprobacion.crs.to_epsg() == 4326
        assert comprobacion.geometry.iloc[0].geom_type == "LineString"
        assert comprobacion.geometry.iloc[0].is_valid
        assert comprobacion.geometry.iloc[0].is_simple
        assert distancia_km > 0.25
        print(
            f"{id_ruta}: {configuracion['nombre']} | nodos={len(referencias)} | "
            f"ida={distancia_km:.3f} km | total={distancia_km * 2:.3f} km"
        )


if __name__ == "__main__":
    main()
