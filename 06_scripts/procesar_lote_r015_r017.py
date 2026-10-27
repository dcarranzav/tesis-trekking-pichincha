"""Construye tres rutas de Mindo y valida sus tramos compartidos."""

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
    "R015": {
        "nombre": "Mindo Hermit Trail - Cascada Corazón",
        "tramos": [
            ("1497391421", f"MINDO_hermit_acceso_osm_{FECHA}.osm", "Mindo Hermit Trail"),
            ("1497391422", f"R015_hermit_cascada_corazon_osm_{FECHA}.osm", "Mindo Hermit Trail - Cascada Corazón"),
        ],
    },
    "R016": {
        "nombre": "Mindo Hermit Trail - Mirador",
        "tramos": [
            ("1497391421", f"MINDO_hermit_acceso_osm_{FECHA}.osm", "Mindo Hermit Trail"),
            ("1497391425", f"R016_hermit_mirador_osm_{FECHA}.osm", "Mindo Hermit Trail - Mirador"),
        ],
    },
    "R017": {
        "nombre": "Yellow House Trail",
        "tramos": [
            ("299595681", f"R017_yellow_house_trail_osm_{FECHA}.osm", "Yellow House Trail"),
        ],
    },
}


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def cargar_via(archivo: Path, id_via: str, nombre_esperado: str) -> tuple[list[str], list[tuple[float, float]], dict]:
    raiz = ET.parse(archivo).getroot()
    nodos = {
        nodo.attrib["id"]: (float(nodo.attrib["lon"]), float(nodo.attrib["lat"]))
        for nodo in raiz.findall("node")
    }
    via = next(elemento for elemento in raiz.findall("way") if elemento.attrib["id"] == id_via)
    referencias = [elemento.attrib["ref"] for elemento in via.findall("nd")]
    etiquetas = {elemento.attrib["k"]: elemento.attrib["v"] for elemento in via.findall("tag")}
    assert etiquetas.get("name") == nombre_esperado
    assert etiquetas.get("highway") in {"path", "track"}
    assert len(referencias) == len(set(referencias))
    return referencias, [nodos[referencia] for referencia in referencias], etiquetas


def main() -> None:
    proyecto = localizar_proyecto()
    originales = proyecto / "02_datos_originales" / "trazados"
    intermedios = proyecto / "03_datos_intermedios" / "trazados"
    intermedios.mkdir(parents=True, exist_ok=True)

    for id_ruta, configuracion in RUTAS.items():
        referencias_totales = []
        coordenadas_totales = []
        ids_vias = []
        escalas = []
        for indice, (id_via, nombre_archivo, nombre_osm) in enumerate(configuracion["tramos"]):
            referencias, coordenadas, etiquetas = cargar_via(originales / nombre_archivo, id_via, nombre_osm)
            if indice:
                assert referencias_totales[-1] == referencias[0], (
                    f"Los tramos de {id_ruta} no comparten el nodo de unión"
                )
                referencias = referencias[1:]
                coordenadas = coordenadas[1:]
            referencias_totales.extend(referencias)
            coordenadas_totales.extend(coordenadas)
            ids_vias.append(id_via)
            escalas.append(etiquetas.get("sac_scale", ""))

        geometria = LineString(coordenadas_totales)
        resultado = gpd.GeoDataFrame(
            [{
                "id_ruta": id_ruta,
                "nombre": configuracion["nombre"],
                "id_vias_osm": "|".join(ids_vias),
                "nodo_inicio": referencias_totales[0],
                "nodo_fin": referencias_totales[-1],
                "tipo_recorrido": "ida_y_vuelta",
                "sac_scale": "|".join(valor for valor in escalas if valor),
                "estado": "trazado_osm_continuo",
                "fecha": FECHA,
                "geometry": geometria,
            }],
            crs="EPSG:4326",
        )
        distancia_km = float(resultado.to_crs(32717).length.iloc[0] / 1000)
        resultado["distancia_ida_km"] = round(distancia_km, 3)
        salida = intermedios / f"{id_ruta}_trazado_ida_continuo_{FECHA}.geojson"
        resultado.to_file(salida, driver="GeoJSON")
        comprobacion = gpd.read_file(salida)
        assert len(comprobacion) == 1
        assert comprobacion.crs.to_epsg() == 4326
        assert comprobacion.geometry.iloc[0].is_valid
        assert comprobacion.geometry.iloc[0].is_simple
        assert distancia_km > 0.5
        print(
            f"{id_ruta}: {configuracion['nombre']} | vías={'|'.join(ids_vias)} | "
            f"nodos={len(referencias_totales)} | ida={distancia_km:.3f} km | total={distancia_km * 2:.3f} km"
        )


if __name__ == "__main__":
    main()
