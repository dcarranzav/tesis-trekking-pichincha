"""Construye y valida las geometrías del primer lote de ampliación."""

from pathlib import Path
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from shapely.geometry import LineString


FECHA = "2026-10-07"
RUTAS = {
    "R008": {
        "nombre": "Sendero de ascenso al Pondoña",
        "id_via": "1057988138",
        "nombre_osm": "Sendero al Pondoña",
        "archivo_original": f"R008_pondona_ascenso_osm_{FECHA}.osm",
        "archivo_intermedio": f"R008_trazado_ida_continuo_{FECHA}.geojson",
        "epsg_metrico": 32617,
        "invertir": True,
    },
    "R009": {
        "nombre": "Sendero Principal de Maquipucuna",
        "id_via": "1329296867",
        "nombre_osm": "Sendero Principal",
        "archivo_original": f"R009_maquipucuna_principal_osm_{FECHA}.osm",
        "archivo_intermedio": f"R009_trazado_ida_continuo_{FECHA}.geojson",
        "epsg_metrico": 32617,
        "invertir": False,
    },
    "R010": {
        "nombre": "Sendero Tranquilo de Maquipucuna",
        "id_via": "1329292949",
        "nombre_osm": "Sendero Tranquilo",
        "archivo_original": f"R010_maquipucuna_tranquilo_osm_{FECHA}.osm",
        "archivo_intermedio": f"R010_trazado_ida_continuo_{FECHA}.geojson",
        "epsg_metrico": 32617,
        "invertir": False,
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
    carpeta_original = proyecto / "02_datos_originales" / "trazados"
    carpeta_intermedia = proyecto / "03_datos_intermedios" / "trazados"
    carpeta_intermedia.mkdir(parents=True, exist_ok=True)

    for id_ruta, configuracion in RUTAS.items():
        archivo_original = carpeta_original / configuracion["archivo_original"]
        raiz = ET.parse(archivo_original).getroot()
        nodos = {
            elemento.attrib["id"]: (
                float(elemento.attrib["lon"]),
                float(elemento.attrib["lat"]),
            )
            for elemento in raiz.findall("node")
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
        assert etiquetas.get("highway") in {"path", "footway"}
        assert len(referencias) == len(set(referencias))
        if configuracion["invertir"]:
            referencias = list(reversed(referencias))
        coordenadas = [nodos[referencia] for referencia in referencias]
        geometria = LineString(coordenadas)
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
                    "estado": "via_osm_completa",
                    "fecha": FECHA,
                    "geometry": geometria,
                }
            ],
            crs="EPSG:4326",
        )
        distancia_km = float(
            resultado.to_crs(configuracion["epsg_metrico"]).length.iloc[0] / 1000
        )
        resultado["distancia_ida_km"] = round(distancia_km, 3)
        archivo_intermedio = carpeta_intermedia / configuracion["archivo_intermedio"]
        resultado.to_file(archivo_intermedio, driver="GeoJSON")

        comprobacion = gpd.read_file(archivo_intermedio)
        assert len(comprobacion) == 1
        assert comprobacion.crs.to_epsg() == 4326
        assert comprobacion.geometry.iloc[0].geom_type == "LineString"
        assert comprobacion.geometry.iloc[0].is_valid
        assert comprobacion.geometry.iloc[0].is_simple
        assert distancia_km > 0.2

        print(f"Ruta: {id_ruta} - {configuracion['nombre']}")
        print(f"Vía OSM: {configuracion['id_via']} - {etiquetas['name']}")
        print(f"Nodos: {len(referencias)}")
        print(f"Distancia de ida: {distancia_km:.3f} km")
        print(f"Distancia ida y vuelta: {distancia_km * 2:.3f} km")
        print(f"Archivo: {archivo_intermedio.name}\n")


if __name__ == "__main__":
    main()
