"""K-means para dificultad física estimada relativa de rutas elegibles.

Modelo principal: distancia total y ascenso acumulado (z-score; igual peso),
k=2, 50 inicializaciones k-means++ y mínimo de inercia. Altitud y pendiente
quedan fuera del ajuste: la primera es contexto de exposición y la segunda
es más sensible al ruido del DEM. Las clases son RELATIVAS a esta muestra;
no certifican apertura, seguridad ni aptitud personal.

Uso: python 06_scripts/evaluar_kmeans_esfuerzo.py --fecha 2026-10-22
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from math import comb
from pathlib import Path
import hashlib
import json
import os
import sys

if sys.platform == "win32":
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"
    os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import DBSCAN, KMeans

RAIZ = Path(__file__).resolve().parents[1]
TABLAS = RAIZ / "07_resultados" / "tablas"
VARIABLES = ("distancia_total_km", "ascenso_total_m")
SEMILLAS = range(50)


def ari(a, b) -> float:
    """Adjusted Rand Index, definido también para particiones con una clase."""
    a, b = np.asarray(a), np.asarray(b)
    if len(a) != len(b) or len(a) < 2:
        raise ValueError("Las particiones requieren el mismo número de rutas (>=2)")
    ga = [set(np.flatnonzero(a == v)) for v in np.unique(a)]
    gb = [set(np.flatnonzero(b == v)) for v in np.unique(b)]
    celdas = sum(comb(len(x & y), 2) for x in ga for y in gb)
    ra = sum(comb(len(x), 2) for x in ga)
    rb = sum(comb(len(y), 2) for y in gb)
    esperado = ra * rb / comb(len(a), 2)
    denominador = (ra + rb) / 2 - esperado
    return float((celdas - esperado) / denominador) if denominador else 1.0


def silueta(x: np.ndarray, etiquetas: np.ndarray) -> float:
    """Silueta media euclídea; los grupos de un elemento aportan cero."""
    grupos = np.unique(etiquetas)
    if len(grupos) < 2 or len(grupos) >= len(x):
        raise ValueError("La silueta requiere al menos dos grupos no triviales")
    distancias = squareform(pdist(x))
    valores = []
    for i in range(len(x)):
        mismos = np.flatnonzero(etiquetas == etiquetas[i])
        if len(mismos) == 1:
            valores.append(0.0)
            continue
        a = distancias[i, mismos[mismos != i]].mean()
        b = min(distancias[i, etiquetas == grupo].mean() for grupo in grupos if grupo != etiquetas[i])
        valores.append(float((b - a) / max(a, b)))
    return float(np.mean(valores))


def escalar(datos: pd.DataFrame, variables=VARIABLES, pesos=None) -> np.ndarray:
    x = datos[list(variables)].to_numpy(float)
    if not np.isfinite(x).all() or np.any(x.std(axis=0) == 0):
        raise ValueError("Faltan datos o alguna variable es constante")
    x = (x - x.mean(axis=0)) / x.std(axis=0)
    if pesos is not None:
        x *= np.asarray(pesos, float)
    return x


def orientar(etiquetas: np.ndarray, datos: pd.DataFrame) -> np.ndarray:
    """0/1 por media creciente del esfuerzo continuo, solo para describir."""
    referencia = datos["distancia_total_km"].to_numpy(float) / 5 + datos["ascenso_total_m"].to_numpy(float) / 600
    orden = sorted(np.unique(etiquetas), key=lambda g: float(referencia[etiquetas == g].mean()))
    mapa = {g: i for i, g in enumerate(orden)}
    return np.asarray([mapa[g] for g in etiquetas], int)


def ajustar(datos: pd.DataFrame, k: int, variables=VARIABLES, pesos=None) -> dict:
    x = escalar(datos, variables, pesos)
    ajustes = []
    for semilla in SEMILLAS:
        modelo = KMeans(n_clusters=k, random_state=semilla, n_init=10).fit(x)
        ajustes.append((float(modelo.inertia_), semilla, modelo.labels_))
    inercia, semilla, etiquetas = min(ajustes, key=lambda a: (a[0], a[1]))
    ward = fcluster(linkage(x, method="ward"), k, criterion="maxclust")
    return {
        "etiquetas": orientar(etiquetas, datos),
        "inercia": inercia,
        "semilla": semilla,
        "silueta": silueta(x, etiquetas),
        "ari_semillas_min": min(ari(etiquetas, a[2]) for a in ajustes),
        "ari_ward": ari(etiquetas, ward),
        "tamano_grupos": sorted(Counter(etiquetas).values()),
        "x": x,
    }


def cargar() -> pd.DataFrame:
    datos = pd.read_csv(TABLAS / "dataset_clasificacion_rutas.csv")
    elegibles = datos.loc[datos.estado_modelado.eq("elegible_actual")].sort_values("id_ruta").reset_index(drop=True)
    if elegibles.empty or not elegibles.id_ruta.is_unique:
        raise ValueError("Muestra elegible vacía o con ID duplicados")
    escalar(elegibles)
    return elegibles


def evaluar(datos: pd.DataFrame, fecha: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    res = {k: ajustar(datos, k) for k in (2, 3, 4)}
    resumen = pd.DataFrame([{
        "k": k, "variables": "|".join(VARIABLES), "n_rutas": len(datos),
        "silueta": round(r["silueta"], 4), "inercia": round(r["inercia"], 4),
        "tamanos": "/".join(map(str, r["tamano_grupos"])),
        "ari_semillas_min": round(r["ari_semillas_min"], 4),
        "ari_ward": round(r["ari_ward"], 4),
    } for k, r in res.items()])
    base = res[2]["etiquetas"]
    escenarios = []

    def contraste(nombre: str, sub: pd.DataFrame, variables=VARIABLES, pesos=None) -> None:
        modelo = ajustar(sub, 2, variables, pesos)
        indice_base = datos.set_index("id_ruta")
        etiquetas_base = [base[indice_base.index.get_loc(r)] for r in sub.id_ruta]
        escenarios.append({"escenario": nombre, "n_rutas": len(sub),
                           "ari_con_base": round(ari(etiquetas_base, modelo["etiquetas"]), 4),
                           "rutas_cambiadas": "|".join(str(r) for r, b, c in zip(sub.id_ruta, etiquetas_base,
                                                    modelo["etiquetas"]) if b != c),
                           "silueta": round(modelo["silueta"], 4)})

    contraste("base", datos)
    for nombre, pesos in (("peso_distancia_mitad", (0.5, 1)), ("peso_distancia_doble", (2, 1)),
                          ("peso_ascenso_mitad", (1, 0.5)), ("peso_ascenso_doble", (1, 2))):
        contraste(nombre, datos, pesos=pesos)
    contraste("con_pendiente_media", datos, VARIABLES + ("pendiente_media_abs_pct",))
    for id_quitar in datos.id_ruta:
        contraste(f"sin_{id_quitar}", datos.loc[datos.id_ruta.ne(id_quitar)].reset_index(drop=True))
    for nombre, ascendente in (("una_por_destino_corta", True), ("una_por_destino_larga", False)):
        sub = (datos.sort_values("distancia_total_km", ascending=ascendente)
               .drop_duplicates("id_destino").sort_values("id_ruta").reset_index(drop=True))
        contraste(nombre, sub)
    dem = TABLAS / f"indicador_dem_perfiles_{fecha}.csv"
    if dem.exists():
        perfiles = pd.read_csv(dem).set_index("id_ruta")
        for nombre, columna in (("ascenso_mediana5", "ascenso_mediana5_m"),
                                ("ascenso_crudo", "ascenso_crudo_m")):
            sub = datos.copy()
            sub["ascenso_total_m"] = perfiles.loc[sub.id_ruta, columna].to_numpy(float)
            contraste(nombre, sub)
    tabla_escenarios = pd.DataFrame(escenarios)
    cambios = {ruta: [] for ruta in datos.id_ruta}
    for fila in escenarios:
        if fila["escenario"] == "base" or fila["escenario"].startswith("sin_") or fila["escenario"].startswith("una_"):
            continue
        for ruta in str(fila["rutas_cambiadas"]).split("|"):
            if ruta:
                cambios[ruta].append(fila["escenario"])
    asignaciones = datos[["id_ruta", "id_destino", "distancia_total_km", "ascenso_total_m",
                          "pendiente_media_abs_pct", "elevacion_max_m"]].copy()
    asignaciones["grupo_relativo_k2"] = base
    asignaciones["etiqueta_descriptiva"] = np.where(base == 1, "Mayor esfuerzo físico estimado relativo",
                                                     "Menor esfuerzo físico estimado relativo")
    asignaciones["escenarios_cambio"] = asignaciones.id_ruta.map(lambda r: "|".join(cambios[r]))
    asignaciones["sensible_a_parametros"] = asignaciones.id_ruta.map(lambda r: "si" if cambios[r] else "no")
    asignaciones["advertencia"] = "Clase relativa al conjunto estudiado; no evalúa acceso, técnica, clima ni seguridad"
    return resumen, tabla_escenarios, asignaciones


def parametros_modelo(datos: pd.DataFrame, asignaciones: pd.DataFrame, fecha: str) -> dict:
    """Guarda escala y centroides para aplicar *el mismo* modelo a otra ruta."""
    x_original = datos[list(VARIABLES)].to_numpy(float)
    medias = x_original.mean(axis=0)
    desv = x_original.std(axis=0)
    x = (x_original - medias) / desv
    etiquetas = asignaciones["grupo_relativo_k2"].to_numpy(int)
    centros = np.array([x[etiquetas == g].mean(axis=0) for g in (0, 1)])
    predichas = np.argmin(((x[:, None, :] - centros[None, :, :]) ** 2).sum(axis=2), axis=1)
    if not np.array_equal(etiquetas, predichas):
        raise ValueError("Los centroides guardados no reproducen las asignaciones")
    return {
        "version": "kmeans-fisico-relativo-v1", "fecha": fecha,
        "algoritmo": "scikit-learn KMeans (k-means++, n_init=10, 50 semillas, mínimo de inercia)",
        "variables": list(VARIABLES), "media_entrenamiento": medias.tolist(),
        "desviacion_entrenamiento": desv.tolist(), "centroides_estandarizados": centros.tolist(),
        "n_rutas": len(datos), "ids_entrenamiento": datos.id_ruta.tolist(),
        "sha256_dataset": hashlib.sha256((TABLAS / "dataset_clasificacion_rutas.csv").read_bytes()).hexdigest(),
        "limite": "Clase relativa a la muestra; no predice seguridad, acceso, técnica ni aptitud personal",
    }


def contraste_dbscan(datos: pd.DataFrame, asignaciones: pd.DataFrame) -> pd.DataFrame:
    """DBSCAN en el mismo espacio 2-D; separa cobertura de acuerdo."""
    x = escalar(datos)
    base = asignaciones["grupo_relativo_k2"].to_numpy(int)
    filas = []
    for eps in (0.3, 0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5):
        for min_samples in (2, 3, 4):
            etiquetas = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(x)
            retenidas = etiquetas != -1
            grupos = len(set(etiquetas) - {-1})
            acuerdo = ari(base[retenidas], etiquetas[retenidas]) if grupos >= 2 and sum(retenidas) >= 2 else ""
            filas.append({
                "eps": eps, "min_samples": min_samples,
                "grupos_dbscan": grupos, "n_ruido": int(sum(~retenidas)),
                "n_comparables": int(sum(retenidas)),
                "ari_con_kmeans_solo_no_ruido": round(acuerdo, 4) if acuerdo != "" else "",
                "rutas_ruido": "|".join(datos.id_ruta[~retenidas]),
                "aviso": "ARI omite rutas ruido: no es concordancia de la muestra completa",
            })
    return pd.DataFrame(filas)


def asignar_nueva_ruta(distancia_total_km: float, ascenso_total_m: float, parametros: dict) -> int:
    """Asigna por centroide más cercano; requiere indicadores calculados igual."""
    valores = np.array([distancia_total_km, ascenso_total_m], float)
    if not np.isfinite(valores).all() or np.any(valores < 0):
        raise ValueError("Distancia o ascenso no válido")
    x = (valores - np.array(parametros["media_entrenamiento"])) / np.array(parametros["desviacion_entrenamiento"])
    centros = np.array(parametros["centroides_estandarizados"])
    return int(np.argmin(((centros - x) ** 2).sum(axis=1)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", required=True)
    args = parser.parse_args()
    fecha = date.fromisoformat(args.fecha).isoformat()
    datos = cargar()
    resumen, escenarios, asignaciones = evaluar(datos, fecha)
    for nombre, tabla in (("modelo_kmeans_fisico_resumen", resumen),
                          ("modelo_kmeans_fisico_sensibilidad", escenarios),
                          ("modelo_kmeans_fisico_asignaciones", asignaciones)):
        tabla.to_csv(TABLAS / f"{nombre}_{fecha}.csv", index=False, encoding="utf-8")
    parametros = parametros_modelo(datos, asignaciones, fecha)
    (TABLAS / f"modelo_kmeans_fisico_parametros_{fecha}.json").write_text(
        json.dumps(parametros, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    contraste_dbscan(datos, asignaciones).to_csv(
        TABLAS / f"modelo_kmeans_fisico_dbscan_{fecha}.csv", index=False, encoding="utf-8"
    )
    print(resumen.to_string(index=False))
    print(f"Rutas sensibles: {sum(asignaciones.sensible_a_parametros.eq('si'))}/{len(asignaciones)}")


if __name__ == "__main__":
    main()
