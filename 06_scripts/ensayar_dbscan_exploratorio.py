"""Contraste exploratorio DBSCAN; nunca publica clases ni recomendaciones."""

from argparse import ArgumentParser
from datetime import date
import os
from pathlib import Path
import sys

# Evita el fallo local de consulta de hilos MKL en Windows.
if sys.platform == "win32":
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "07_resultados/tablas/dataset_clasificacion_rutas.csv"
VARIABLES = (
    "distancia_total_km",
    "ascenso_total_m",
    "elevacion_max_m",
    "pendiente_media_abs_pct",
)
EPSILON = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
MIN_SAMPLES = (2, 3)


def cargar_datos(ruta: Path = ENTRADA) -> pd.DataFrame:
    datos = pd.read_csv(ruta)
    elegibles = datos.loc[datos["estado_modelado"].eq("elegible_actual")].copy()
    if len(elegibles) < 3 or not elegibles["id_ruta"].is_unique:
        raise ValueError("Se requieren al menos tres rutas elegibles con ID únicos")
    for variable in VARIABLES:
        elegibles[variable] = pd.to_numeric(elegibles[variable], errors="coerce")
    if not np.isfinite(elegibles[list(VARIABLES)].to_numpy()).all():
        raise ValueError("Las variables físicas contienen valores no finitos")
    return elegibles.sort_values("id_ruta").reset_index(drop=True)


def evaluar(datos: pd.DataFrame, epsilon=EPSILON, min_samples=MIN_SAMPLES):
    """Devuelve métricas y etiquetas; -1 es ruido, no una clase de esfuerzo."""
    escalados = StandardScaler().fit_transform(datos[list(VARIABLES)])
    metricas, asignaciones = [], []
    for minimo in min_samples:
        for radio in epsilon:
            etiquetas = DBSCAN(eps=radio, min_samples=minimo).fit_predict(escalados)
            agrupados = etiquetas != -1
            grupos = np.unique(etiquetas[agrupados])
            tamanos = np.bincount(etiquetas[agrupados]) if agrupados.any() else np.array([])
            # La silueta se calcula solo cuando hay al menos dos grupos no ruido.
            silueta = (
                float(silhouette_score(escalados[agrupados], etiquetas[agrupados]))
                if 2 <= len(grupos) < int(agrupados.sum())
                else np.nan
            )
            metricas.append({
                "eps": radio,
                "min_samples": minimo,
                "n_rutas": len(datos),
                "n_grupos": len(grupos),
                "n_ruido": int((~agrupados).sum()),
                "cobertura_pct": round(100 * float(agrupados.mean()), 1),
                "tamano_minimo_grupo": int(tamanos.min()) if len(tamanos) else 0,
                "silueta_sin_ruido": round(silueta, 4) if np.isfinite(silueta) else np.nan,
            })
            for id_ruta, etiqueta in zip(datos["id_ruta"], etiquetas):
                asignaciones.append({
                    "eps": radio,
                    "min_samples": minimo,
                    "id_ruta": id_ruta,
                    "grupo_numerico_sin_orden": int(etiqueta),
                })
    return pd.DataFrame(metricas), pd.DataFrame(asignaciones)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", required=True, help="Fecha real de ejecución, AAAA-MM-DD")
    parser.add_argument("--identificador", default="", help="Sufijo opcional para conservar cortes del mismo día")
    args = parser.parse_args()
    fecha = date.fromisoformat(args.fecha).isoformat()
    identificador = args.identificador.strip()
    if identificador and not (identificador.isascii() and identificador.replace("_", "").isalnum()):
        parser.error("--identificador solo admite letras, números y guiones bajos ASCII")
    datos = cargar_datos()
    metricas, asignaciones = evaluar(datos)
    nombre = f"dbscan_exploratorio_{fecha}" + (f"_{identificador}" if identificador else "")
    salida = RAIZ / "07_resultados/tablas"
    metricas.to_csv(salida / f"evaluacion_{nombre}.csv", index=False)
    asignaciones.to_csv(salida / f"grupos_{nombre}.csv", index=False)
    lineas = [
        "# Contraste exploratorio DBSCAN",
        "",
        f"Fecha: {fecha}. Muestra: {len(datos)} rutas elegibles provisionales.",
        "",
        "Se usan las mismas cuatro variables físicas base del ensayo K-means, estandarizadas con StandardScaler. "
        "La distancia es euclidiana. La cuadrícula fija de eps y min_samples es una prueba de sensibilidad, "
        "no una búsqueda del máximo de silueta ni una selección de modelo final.",
        "",
        "| eps | min_samples | grupos | ruido | cobertura | silueta sin ruido |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for fila in metricas.itertuples(index=False):
        silueta = f"{fila.silueta_sin_ruido:.3f}" if np.isfinite(fila.silueta_sin_ruido) else "—"
        lineas.append(
            f"| {fila.eps:g} | {fila.min_samples} | {fila.n_grupos} | "
            f"{fila.n_ruido} | {fila.cobertura_pct:.1f}% | {silueta} |"
        )
    lineas += [
        "",
        "`-1` significa ruido estadístico: **no** implica peligro, dificultad alta ni exclusión de la ruta. "
        "La silueta omite el ruido y por eso debe leerse junto con la cobertura; no es directamente "
        "comparable con la silueta K-means de todas las rutas.",
        "",
        "Con una muestra pequeña, los grupos cambian al variar eps y min_samples. "
        "DBSCAN no reemplaza el ensayo K-means/Ward ni permite etiquetar los grupos como dificultad baja, "
        "media o alta. No se modifican inventario, dataset, interfaz ni compuerta de recomendación.",
        "",
        f"Reproducir: `python 06_scripts/ensayar_dbscan_exploratorio.py --fecha {fecha}"
        + (f" --identificador {identificador}" if identificador else "") + "`.",
        "",
    ]
    (RAIZ / "01_documentacion" / f"ensayo_{nombre}.md").write_text(
        "\n".join(lineas), encoding="utf-8"
    )
    print(metricas.to_string(index=False))


if __name__ == "__main__":
    main()
