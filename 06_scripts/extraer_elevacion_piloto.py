"""Extrae perfiles de elevación Copernicus GLO-30 para las rutas piloto."""

from argparse import ArgumentParser
from pathlib import Path
import os
import sys

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import numpy as np
import pandas as pd
import rasterio
import geopandas as gpd


FECHA = "2026-10-05"
PASO_M = 30.0
ARCHIVOS_RUTA = {
    "R001": "R001_trazado_subida_cumbre_2026-10-05.geojson",
    "R003": "R003_trazado_ida_continuo_2026-10-01.geojson",
    "R005": "R005_trazado_preliminar_2026-10-01.geojson",
    "R006": "R006_trazado_ida_continuo_2026-10-05.geojson",
}


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def extraer_perfil(id_ruta: str) -> Path:
    proyecto = localizar_proyecto()
    archivo_ruta = (
        proyecto
        / "03_datos_intermedios"
        / "trazados"
        / ARCHIVOS_RUTA[id_ruta]
    )
    archivo_dem = (
        proyecto
        / "02_datos_originales"
        / "elevacion"
        / "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif"
    )
    carpeta_salida = proyecto / "03_datos_intermedios" / "elevacion"
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    archivo_salida = (
        carpeta_salida
        / f"{id_ruta}_perfil_elevacion_raw_{FECHA}.csv"
    )

    ruta = gpd.read_file(archivo_ruta)
    assert len(ruta) == 1
    assert ruta.crs.to_epsg() == 4326
    geometria_utm = ruta.to_crs(32717).geometry.iloc[0]
    longitud_m = float(geometria_utm.length)

    numero_tramos = int(np.ceil(longitud_m / PASO_M))
    distancias = np.linspace(0.0, longitud_m, numero_tramos + 1)

    puntos_utm = gpd.GeoSeries(
        [geometria_utm.interpolate(float(d)) for d in distancias],
        crs="EPSG:32717",
    )
    puntos_wgs84 = puntos_utm.to_crs(4326)
    coordenadas = [(p.x, p.y) for p in puntos_wgs84]

    with rasterio.open(archivo_dem) as dem:
        assert dem.crs.to_epsg() == 4326
        resolucion_x, resolucion_y = dem.res
        columnas = np.floor(
            [(x - dem.bounds.left) / resolucion_x for x, _ in coordenadas]
        ).astype(int)
        filas = np.floor(
            [(dem.bounds.top - y) / resolucion_y for _, y in coordenadas]
        ).astype(int)
        assert ((columnas >= 0) & (columnas < dem.width)).all()
        assert ((filas >= 0) & (filas < dem.height)).all()
        banda = dem.read(1)
        elevaciones = banda[filas, columnas].astype(float)

    perfil = pd.DataFrame(
        {
            "id_ruta": id_ruta,
            "orden": np.arange(len(distancias)),
            "distancia_m": np.round(distancias, 3),
            "longitud": [round(p.x, 8) for p in puntos_wgs84],
            "latitud": [round(p.y, 8) for p in puntos_wgs84],
            "elevacion_m": np.round(elevaciones, 3),
            "fuente_elevacion": "Copernicus DEM GLO-30 Public 2021",
        }
    )
    perfil.to_csv(archivo_salida, index=False, encoding="utf-8")

    faltantes = int(perfil["elevacion_m"].isna().sum())
    diferencias = perfil["elevacion_m"].diff()
    ascenso_raw = float(diferencias.clip(lower=0).sum())

    print("Ruta:", id_ruta)
    print("Archivo del trazado:", archivo_ruta.name)
    print("Archivo DEM:", archivo_dem.name)
    print("Longitud del trazado:", round(longitud_m / 1000, 3), "km")
    print(
        "Intervalo real de muestreo:",
        round(float(np.diff(distancias).mean()), 3),
        "m",
    )
    print("Puntos del perfil:", len(perfil))
    print("Valores faltantes:", faltantes)
    print("Elevación mínima raw:", round(perfil["elevacion_m"].min(), 1), "m")
    print("Elevación máxima raw:", round(perfil["elevacion_m"].max(), 1), "m")
    print("Ascenso acumulado raw:", round(ascenso_raw, 1), "m")
    print("Archivo guardado:", archivo_salida.name)

    assert faltantes == 0
    assert perfil["orden"].is_unique
    assert perfil["distancia_m"].is_monotonic_increasing
    assert len(perfil) >= 2
    assert perfil["elevacion_m"].between(-500, 7000).all()

    return archivo_salida


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--ruta", choices=sorted(ARCHIVOS_RUTA), required=True)
    argumentos = parser.parse_args()
    extraer_perfil(argumentos.ruta)
