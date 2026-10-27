"""Extrae, filtra y resume la elevación de las rutas de ampliación."""

from argparse import ArgumentParser
from pathlib import Path
import os
import sys

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio


PASO_M = 30.0
RUTAS = {
    "R002": {
        "nombre": "Sendero Los Pantzas",
        "fecha": "2026-10-06",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R002_trazado_ida_continuo_2026-10-06.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R004": {
        "nombre": "Circuito Pondoña",
        "fecha": "2026-10-06",
        "tipo_recorrido": "circular",
        "archivo_trazado": "R004_trazado_circular_continuo_2026-10-06.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif",
        "epsg_metrico": 32617,
    },
    "R007": {
        "nombre": "Sendero sur al volcán El Corazón",
        "fecha": "2026-10-06",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R007_trazado_ida_continuo_2026-10-06.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R008": {
        "nombre": "Sendero de ascenso al Pondoña",
        "fecha": "2026-10-07",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R008_trazado_ida_continuo_2026-10-07.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif",
        "epsg_metrico": 32617,
    },
    "R009": {
        "nombre": "Sendero Principal de Maquipucuna",
        "fecha": "2026-10-07",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R009_trazado_ida_continuo_2026-10-07.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif",
        "epsg_metrico": 32617,
    },
    "R010": {
        "nombre": "Sendero Tranquilo de Maquipucuna",
        "fecha": "2026-10-07",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R010_trazado_ida_continuo_2026-10-07.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif",
        "epsg_metrico": 32617,
    },
    "R011": {
        "nombre": "Sendero Masked Trogon",
        "fecha": "2026-10-09",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R011_trazado_ida_continuo_2026-10-09.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R012": {
        "nombre": "Sendero Andean Snipe",
        "fecha": "2026-10-09",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R012_trazado_ida_continuo_2026-10-09.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R013": {
        "nombre": "Sendero Oso de Anteojos",
        "fecha": "2026-10-09",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R013_trazado_ida_continuo_2026-10-09.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R014": {
        "nombre": "Trocha Inca",
        "fecha": "2026-10-09",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R014_trazado_ida_continuo_2026-10-09.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R015": {
        "nombre": "Mindo Hermit Trail - Cascada Corazón",
        "fecha": "2026-10-09",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R015_trazado_ida_continuo_2026-10-09.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R016": {
        "nombre": "Mindo Hermit Trail - Mirador",
        "fecha": "2026-10-09",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R016_trazado_ida_continuo_2026-10-09.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R017": {
        "nombre": "Yellow House Trail",
        "fecha": "2026-10-09",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R017_trazado_ida_continuo_2026-10-09.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R018": {
        "nombre": "Sendero de la Cascada de Maquipucuna",
        "fecha": "2026-10-10",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R018_trazado_ida_continuo_2026-10-10.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif",
        "epsg_metrico": 32617,
    },
    "R019": {
        "nombre": "Sendero Tarabita - Cascada La Reina",
        "fecha": "2026-10-12",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R019_trazado_ida_continuo_2026-10-12.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R020": {
        "nombre": "Yellow House Trail vía Sendero 3",
        "fecha": "2026-10-14",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R020_trazado_ida_continuo_2026-10-14.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R021": {
        "nombre": "Yellow House Trail vía Senderos 1 y 2",
        "fecha": "2026-10-17",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R021_trazado_ida_continuo_2026-10-17.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R022": {
        "nombre": "Camino a la Cruz del Ilaló desde Los Olivos",
        "fecha": "2026-10-17",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R022_trazado_ida_continuo_2026-10-17.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R023": {
        "nombre": "Sendero a Cascada Guagrapamba",
        "fecha": "2026-10-21",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R023_trazado_ida_continuo_2026-10-21.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R024": {
        "nombre": "Cerro de la Luz - sendero directo al mirador",
        "fecha": "2026-10-21",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R024_trazado_ida_continuo_2026-10-21.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif",
        "epsg_metrico": 32617,
    },
    "R025": {
        "nombre": "Cerro de la Luz - sendero superior al mirador",
        "fecha": "2026-10-21",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R025_trazado_ida_continuo_2026-10-21.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif",
        "epsg_metrico": 32617,
    },
    "R026": {
        "nombre": "Tarabita - Cascada Guarumos",
        "fecha": "2026-10-22",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R026_trazado_ida_continuo_2026-10-22.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
        "epsg_metrico": 32717,
    },
    "R027": {
        "nombre": "Sendero del Viento - sector recreativo Moraspungo",
        "fecha": "2026-10-22",
        "tipo_recorrido": "ida_y_vuelta",
        "archivo_trazado": "R027_trazado_ida_continuo_2026-10-22.geojson",
        "archivo_dem": "Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif",
        "epsg_metrico": 32617,
    },
}

parser = ArgumentParser()
parser.add_argument("--ruta", choices=sorted(RUTAS), required=True)
argumentos = parser.parse_args()
ID_RUTA = argumentos.ruta
NOMBRE = RUTAS[ID_RUTA]["nombre"]
FECHA = RUTAS[ID_RUTA]["fecha"]
TIPO_RECORRIDO = RUTAS[ID_RUTA]["tipo_recorrido"]
NOMBRE_ARCHIVO_TRAZADO = RUTAS[ID_RUTA]["archivo_trazado"]
NOMBRE_ARCHIVO_DEM = RUTAS[ID_RUTA]["archivo_dem"]
EPSG_METRICO = RUTAS[ID_RUTA]["epsg_metrico"]


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def mediana_centrada(valores: np.ndarray, ventana: int) -> np.ndarray:
    radio = ventana // 2
    resultado = np.array(
        [
            np.median(
                valores[max(0, i - radio) : min(len(valores), i + radio + 1)]
            )
            for i in range(len(valores))
        ],
        dtype=float,
    )
    resultado[0] = valores[0]
    resultado[-1] = valores[-1]
    return resultado


def calcular_indicadores(elevacion: np.ndarray, distancias: np.ndarray) -> dict:
    cambio_elevacion = np.diff(elevacion)
    cambio_distancia = np.diff(distancias)
    pendientes = cambio_elevacion / cambio_distancia * 100
    ascenso_trazado = float(cambio_elevacion[cambio_elevacion > 0].sum())
    descenso_trazado = float(-cambio_elevacion[cambio_elevacion < 0].sum())
    return {
        "elevacion_min_m": float(elevacion.min()),
        "elevacion_max_m": float(elevacion.max()),
        "ascenso_trazado_m": ascenso_trazado,
        "descenso_trazado_m": descenso_trazado,
        "desnivel_acumulado_trazado_m": ascenso_trazado + descenso_trazado,
        "pendiente_media_abs_pct": float(
            np.abs(cambio_elevacion).sum() / cambio_distancia.sum() * 100
        ),
        "pendiente_p95_abs_pct": float(np.percentile(np.abs(pendientes), 95)),
        "pendiente_max_abs_pct": float(np.abs(pendientes).max()),
    }


def guardar_acumulado(
    nuevos: pd.DataFrame, archivo: Path, decimales: int
) -> pd.DataFrame:
    """Actualiza solo la ruta procesada y conserva las demás rutas."""
    if archivo.exists():
        anteriores = pd.read_csv(archivo)
        anteriores = anteriores[~anteriores["id_ruta"].isin(nuevos["id_ruta"])]
        resultado = pd.concat([anteriores, nuevos], ignore_index=True)
    else:
        resultado = nuevos.copy()
    resultado = resultado.dropna(axis=1, how="all")
    columnas_orden = [
        columna
        for columna in ("id_ruta", "metodo", "orden_fin")
        if columna in resultado.columns
    ]
    resultado = resultado.sort_values(columnas_orden).reset_index(drop=True)
    resultado.round(decimales).to_csv(archivo, index=False, encoding="utf-8")
    return resultado


def puntos_svg(x, y, izquierda, arriba, ancho, alto, xmin, xmax, ymin, ymax):
    puntos = []
    for valor_x, valor_y in zip(x, y):
        px = izquierda + (valor_x - xmin) / (xmax - xmin) * ancho
        py = arriba + alto - (valor_y - ymin) / (ymax - ymin) * alto
        puntos.append(f"{px:.1f},{py:.1f}")
    return " ".join(puntos)


def guardar_svg(perfil: pd.DataFrame, archivo_salida: Path) -> None:
    x = perfil["distancia_m"] / 1000
    raw = perfil["elevacion_m"]
    filtrada = perfil["elevacion_mediana3_m"]
    xmin, xmax = 0.0, float(x.max())
    margen_y = max(20.0, float(raw.max() - raw.min()) * 0.08)
    ymin = float(min(raw.min(), filtrada.min()) - margen_y)
    ymax = float(max(raw.max(), filtrada.max()) + margen_y)
    izquierda, arriba, ancho, alto = 85, 70, 850, 340
    raw_pts = puntos_svg(x, raw, izquierda, arriba, ancho, alto, xmin, xmax, ymin, ymax)
    filtrada_pts = puntos_svg(
        x, filtrada, izquierda, arriba, ancho, alto, xmin, xmax, ymin, ymax
    )

    lineas = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="500" viewBox="0 0 1000 500">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="500" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">{ID_RUTA} – {NOMBRE}</text>',
        '<text x="500" y="52" text-anchor="middle" font-family="Arial" font-size="13">Perfil Copernicus DEM GLO-30 · muestreo cada 30 m</text>',
    ]
    for i in range(6):
        valor = ymin + (ymax - ymin) * i / 5
        py = arriba + alto - alto * i / 5
        lineas.append(f'<line x1="{izquierda}" y1="{py:.1f}" x2="{izquierda+ancho}" y2="{py:.1f}" stroke="#dddddd"/>')
        lineas.append(f'<text x="{izquierda-10}" y="{py+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{valor:.0f}</text>')
    for i in range(6):
        valor = xmax * i / 5
        px = izquierda + ancho * i / 5
        lineas.append(f'<line x1="{px:.1f}" y1="{arriba}" x2="{px:.1f}" y2="{arriba+alto}" stroke="#eeeeee"/>')
        lineas.append(f'<text x="{px:.1f}" y="{arriba+alto+22}" text-anchor="middle" font-family="Arial" font-size="11">{valor:.1f}</text>')
    lineas.extend(
        [
            f'<polyline points="{raw_pts}" fill="none" stroke="#999999" stroke-width="1.5" opacity="0.8"/>',
            f'<polyline points="{filtrada_pts}" fill="none" stroke="#1769aa" stroke-width="2.5"/>',
            f'<line x1="{izquierda}" y1="{arriba+alto}" x2="{izquierda+ancho}" y2="{arriba+alto}" stroke="#333333"/>',
            f'<line x1="{izquierda}" y1="{arriba}" x2="{izquierda}" y2="{arriba+alto}" stroke="#333333"/>',
            '<text x="510" y="480" text-anchor="middle" font-family="Arial" font-size="13">Distancia del trazado (km)</text>',
            '<text x="20" y="240" text-anchor="middle" transform="rotate(-90 20 240)" font-family="Arial" font-size="13">Elevación (m)</text>',
            '<line x1="665" y1="85" x2="705" y2="85" stroke="#999999" stroke-width="2"/><text x="715" y="89" font-family="Arial" font-size="12">Raw</text>',
            '<line x1="785" y1="85" x2="825" y2="85" stroke="#1769aa" stroke-width="3"/><text x="835" y="89" font-family="Arial" font-size="12">Mediana 3</text>',
            '</svg>',
        ]
    )
    archivo_salida.write_text("\n".join(lineas), encoding="utf-8")


proyecto = localizar_proyecto()
archivo_ruta = (
    proyecto
    / "03_datos_intermedios"
    / "trazados"
    / NOMBRE_ARCHIVO_TRAZADO
)
archivo_dem = (
    proyecto
    / "02_datos_originales"
    / "elevacion"
    / NOMBRE_ARCHIVO_DEM
)
archivo_raw = (
    proyecto
    / "03_datos_intermedios"
    / "elevacion"
    / f"{ID_RUTA}_perfil_elevacion_raw_{FECHA}.csv"
)
archivo_procesado = (
    proyecto
    / "04_datos_procesados"
    / "perfiles"
    / f"{ID_RUTA}_perfil_elevacion_procesado_{FECHA}.csv"
)
carpeta_tablas = proyecto / "07_resultados" / "tablas"
archivo_indicadores = carpeta_tablas / "indicadores_elevacion_ampliacion.csv"
archivo_sensibilidad = carpeta_tablas / "sensibilidad_elevacion_ampliacion.csv"
archivo_extremos = carpeta_tablas / "tramos_pendiente_extrema_ampliacion.csv"
archivo_svg = (
    proyecto
    / "07_resultados"
    / "perfiles"
    / f"{ID_RUTA}_perfil_elevacion_{FECHA}.svg"
)

archivo_raw.parent.mkdir(parents=True, exist_ok=True)
archivo_procesado.parent.mkdir(parents=True, exist_ok=True)
carpeta_tablas.mkdir(parents=True, exist_ok=True)
archivo_svg.parent.mkdir(parents=True, exist_ok=True)

ruta = gpd.read_file(archivo_ruta)
assert len(ruta) == 1
assert ruta.crs.to_epsg() == 4326
geometria_utm = ruta.to_crs(EPSG_METRICO).geometry.iloc[0]
longitud_m = float(geometria_utm.length)
numero_tramos = int(np.ceil(longitud_m / PASO_M))
distancias = np.linspace(0.0, longitud_m, numero_tramos + 1)
puntos_utm = gpd.GeoSeries(
    [geometria_utm.interpolate(float(distancia)) for distancia in distancias],
    crs=f"EPSG:{EPSG_METRICO}",
)
puntos_wgs84 = puntos_utm.to_crs(4326)
coordenadas = [(punto.x, punto.y) for punto in puntos_wgs84]

with rasterio.open(archivo_dem) as dem:
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
        "id_ruta": ID_RUTA,
        "orden": np.arange(len(distancias)),
        "distancia_m": np.round(distancias, 3),
        "longitud": [round(p.x, 8) for p in puntos_wgs84],
        "latitud": [round(p.y, 8) for p in puntos_wgs84],
        "elevacion_m": np.round(elevaciones, 3),
        "fuente_elevacion": "Copernicus DEM GLO-30 Public 2021",
        "archivo_dem": NOMBRE_ARCHIVO_DEM,
    }
)
perfil.to_csv(archivo_raw, index=False, encoding="utf-8")

elevacion_raw = perfil["elevacion_m"].to_numpy(float)
elevacion_mediana3 = mediana_centrada(elevacion_raw, 3)
elevacion_mediana5 = mediana_centrada(elevacion_raw, 5)
perfil["elevacion_mediana3_m"] = np.round(elevacion_mediana3, 3)
perfil["cambio_elevacion_m"] = np.round(
    np.insert(np.diff(elevacion_mediana3), 0, np.nan), 3
)
perfil["pendiente_pct"] = np.round(
    np.insert(np.diff(elevacion_mediana3) / np.diff(distancias) * 100, 0, np.nan),
    3,
)
perfil["metodo_filtrado"] = "mediana_centrada_3_puntos_extremos_conservados"
perfil.to_csv(archivo_procesado, index=False, encoding="utf-8")

principal = calcular_indicadores(elevacion_mediana3, distancias)
if TIPO_RECORRIDO == "ida_y_vuelta":
    distancia_total_km = longitud_m * 2 / 1000
    ascenso_total_m = (
        principal["ascenso_trazado_m"] + principal["descenso_trazado_m"]
    )
elif TIPO_RECORRIDO == "circular":
    distancia_total_km = longitud_m / 1000
    ascenso_total_m = principal["ascenso_trazado_m"]
else:
    raise ValueError(f"Tipo de recorrido no soportado: {TIPO_RECORRIDO}")

indicadores = pd.DataFrame(
    [
        {
            "id_ruta": ID_RUTA,
            "tipo_recorrido": TIPO_RECORRIDO,
            "archivo_dem": NOMBRE_ARCHIVO_DEM,
            "distancia_trazado_km": longitud_m / 1000,
            "distancia_total_km": distancia_total_km,
            "puntos_perfil": len(perfil),
            "valores_faltantes": int(perfil["elevacion_m"].isna().sum()),
            "metodo_principal": "mediana_centrada_3_puntos_extremos_conservados",
            "ascenso_total_m": ascenso_total_m,
            **principal,
        }
    ]
).round(3)
indicadores_acumulados = guardar_acumulado(indicadores, archivo_indicadores, 3)

sensibilidad = []
for metodo, elevacion in (
    ("raw", elevacion_raw),
    ("mediana_3", elevacion_mediana3),
    ("mediana_5", elevacion_mediana5),
):
    indicadores_metodo = calcular_indicadores(elevacion, distancias)
    if TIPO_RECORRIDO == "ida_y_vuelta":
        ascenso_total_metodo = (
            indicadores_metodo["ascenso_trazado_m"]
            + indicadores_metodo["descenso_trazado_m"]
        )
    else:
        ascenso_total_metodo = indicadores_metodo["ascenso_trazado_m"]
    sensibilidad.append(
        {
            "id_ruta": ID_RUTA,
            "tipo_recorrido": TIPO_RECORRIDO,
            "metodo": metodo,
            "ascenso_total_m": ascenso_total_metodo,
            **indicadores_metodo,
        }
    )
sensibilidad_acumulada = guardar_acumulado(
    pd.DataFrame(sensibilidad), archivo_sensibilidad, 3
)

indices_extremos = perfil["pendiente_pct"].abs().nlargest(5).index.tolist()
extremos = []
for indice in indices_extremos:
    extremos.append(
        {
            "id_ruta": ID_RUTA,
            "orden_fin": int(perfil.loc[indice, "orden"]),
            "distancia_inicio_m": float(perfil.loc[indice - 1, "distancia_m"]),
            "distancia_fin_m": float(perfil.loc[indice, "distancia_m"]),
            "elevacion_inicio_m": float(elevacion_mediana3[indice - 1]),
            "elevacion_fin_m": float(elevacion_mediana3[indice]),
            "cambio_elevacion_m": float(perfil.loc[indice, "cambio_elevacion_m"]),
            "pendiente_pct": float(perfil.loc[indice, "pendiente_pct"]),
            "longitud_fin": float(perfil.loc[indice, "longitud"]),
            "latitud_fin": float(perfil.loc[indice, "latitud"]),
        }
    )
extremos_acumulados = guardar_acumulado(
    pd.DataFrame(extremos), archivo_extremos, 6
)

guardar_svg(perfil, archivo_svg)

print("Ruta:", ID_RUTA)
print("Tipo de recorrido:", TIPO_RECORRIDO)
print("Longitud del trazado:", round(longitud_m / 1000, 3), "km")
print("Distancia total:", round(distancia_total_km, 3), "km")
print("Puntos del perfil:", len(perfil))
print("Valores faltantes:", int(perfil["elevacion_m"].isna().sum()))
print("Elevación mínima filtrada:", round(principal["elevacion_min_m"], 1), "m")
print("Elevación máxima filtrada:", round(principal["elevacion_max_m"], 1), "m")
print("Ascenso total:", round(ascenso_total_m, 1), "m")
print("Pendiente p95 absoluta:", round(principal["pendiente_p95_abs_pct"], 1), "%")
print("Perfil gráfico:", archivo_svg.name)

assert indicadores.loc[0, "valores_faltantes"] == 0
assert indicadores.loc[0, "puntos_perfil"] >= 2
assert principal["elevacion_max_m"] > principal["elevacion_min_m"]
assert perfil["distancia_m"].is_monotonic_increasing
assert len(indices_extremos) == 5
assert archivo_svg.exists()
assert indicadores_acumulados["id_ruta"].is_unique
assert sensibilidad_acumulada.groupby("id_ruta").size().eq(3).all()
assert extremos_acumulados.groupby("id_ruta").size().eq(5).all()

print(f"Elevación de {ID_RUTA} procesada y validada correctamente")
