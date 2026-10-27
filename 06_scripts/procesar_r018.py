"""Construye y valida el Sendero de la Cascada de Maquipucuna."""

from pathlib import Path
import os
import sys
import xml.etree.ElementTree as ET

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
from shapely.geometry import LineString


FECHA = "2026-10-10"
ID_RUTA = "R018"
ID_VIA = "801959483"
NOMBRE = "Sendero de la Cascada de Maquipucuna"
NOMBRE_OSM = "Sendero de la Cascada"
ARCHIVO_ORIGINAL = f"R018_maquipucuna_cascada_osm_{FECHA}.osm"


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def main() -> None:
    proyecto = localizar_proyecto()
    archivo = proyecto / "02_datos_originales" / "trazados" / ARCHIVO_ORIGINAL
    raiz = ET.parse(archivo).getroot()
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
        if elemento.attrib["id"] == ID_VIA
    )
    referencias = [elemento.attrib["ref"] for elemento in via.findall("nd")]
    etiquetas = {
        elemento.attrib["k"]: elemento.attrib["v"]
        for elemento in via.findall("tag")
    }
    assert etiquetas.get("name") == NOMBRE_OSM
    assert etiquetas.get("highway") == "path"
    assert etiquetas.get("surface") == "earth"
    assert len(referencias) == len(set(referencias))

    geometria = LineString([nodos[referencia] for referencia in referencias])
    resultado = gpd.GeoDataFrame(
        [
            {
                "id_ruta": ID_RUTA,
                "nombre": NOMBRE,
                "id_via_osm": ID_VIA,
                "nombre_osm": etiquetas["name"],
                "nodo_inicio": referencias[0],
                "nodo_fin": referencias[-1],
                "tipo_recorrido": "ida_y_vuelta",
                "estado": "via_osm_completa_validada_con_fuente_documental",
                "fecha": FECHA,
                "geometry": geometria,
            }
        ],
        crs="EPSG:4326",
    )
    distancia_km = float(resultado.to_crs(32617).length.iloc[0] / 1000)
    resultado["distancia_ida_km"] = round(distancia_km, 3)
    salida = (
        proyecto
        / "03_datos_intermedios"
        / "trazados"
        / f"{ID_RUTA}_trazado_ida_continuo_{FECHA}.geojson"
    )
    salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_file(salida, driver="GeoJSON")

    comprobacion = gpd.read_file(salida)
    assert len(comprobacion) == 1
    assert comprobacion.crs.to_epsg() == 4326
    assert comprobacion.geometry.iloc[0].geom_type == "LineString"
    assert comprobacion.geometry.iloc[0].is_valid
    assert comprobacion.geometry.iloc[0].is_simple
    assert 0.20 <= distancia_km <= 0.35
    print(
        f"{ID_RUTA}: {NOMBRE} | nodos={len(referencias)} | "
        f"ida={distancia_km:.3f} km | total={distancia_km * 2:.3f} km"
    )


if __name__ == "__main__":
    main()
