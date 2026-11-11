"""Experimento K-means k=3 para dificultad física estimada (20 rutas elegibles).

Evalúa si K-means con k=3 sobre distancia total y ascenso total forma tres grupos
físicos coherentes y estables. NO modifica la clasificación pública (regla de
esfuerzo adaptada de MIDE) ni los resultados del 22/23 de octubre: solo escribe
archivos nuevos ``kmeans_k3_*``. Diseño y criterios de aceptación fijados antes de
ejecutar en ``01_documentacion/diseno_experimento_kmeans_k3_2026-11-10.md``.

Los grupos describen esfuerzo físico estimado RELATIVO a estas 20 rutas; no miden
seguridad, dificultad técnica, acceso, clima ni aptitud personal.

Uso: python 06_scripts/evaluar_kmeans_k3_dificultad.py --fecha 2026-11-10
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
from datetime import date
from itertools import product
from pathlib import Path

if sys.platform == "win32":
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"
    os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.stats import spearmanr
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_samples, silhouette_score

RAIZ = Path(__file__).resolve().parents[1]
TABLAS = RAIZ / "07_resultados" / "tablas"
DOCS = RAIZ / "01_documentacion"
VARIABLES = ("distancia_total_km", "ascenso_total_m")
SEMILLAS = tuple(range(50))
N_INIT = 10
K_EVALUADOS = (2, 3, 4)
NOMBRES_GRUPO = {0: "G1 menor esfuerzo relativo", 1: "G2 esfuerzo intermedio relativo", 2: "G3 mayor esfuerzo relativo"}
UMBRAL_SILUETA_INDIVIDUAL = 0.35
UMBRAL_MARGEN_RELATIVO = 0.25
RUTAS_A_REVISAR = ("R001", "R003", "R006", "R017", "R019", "R020", "R021", "R022")


def _modulo(nombre: str, archivo: str):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "06_scripts" / archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# ---------------------------------------------------------------- datos ----

def cargar() -> pd.DataFrame:
    """20 elegibles, con el esfuerzo estimado y el nivel de la regla vigente."""
    dataset = pd.read_csv(TABLAS / "dataset_clasificacion_rutas.csv")
    if len(dataset) != 27 or dataset.estado_modelado.eq("elegible_actual").sum() != 20:
        raise ValueError("Se esperaban 27 rutas procesadas y 20 elegibles")
    datos = dataset.loc[dataset.estado_modelado.eq("elegible_actual")].sort_values("id_ruta").reset_index(drop=True)
    regla = pd.read_csv(TABLAS / "clasificacion_dificultad_fisica_2026-10-23.csv")
    if set(regla.id_ruta) != set(datos.id_ruta) or not datos.id_ruta.is_unique:
        raise ValueError("Las 20 rutas del dataset y de la regla vigente no coinciden")
    datos = datos.merge(
        regla[["id_ruta", "horas_marcha_efectiva_estimadas", "nivel_orden", "dificultad_fisica_estimada"]],
        on="id_ruta", validate="one_to_one",
    )
    dem = pd.read_csv(TABLAS / "indicador_dem_perfiles_2026-10-22.csv").set_index("id_ruta")
    for columna in ("ascenso_mediana3_m", "ascenso_mediana5_m", "ascenso_crudo_m"):
        datos[columna] = dem.loc[datos.id_ruta, columna].to_numpy(float)
    exactos = pd.read_csv(DOCS / "destinos_exactos_interfaz.csv", encoding="utf-8-sig")
    datos = datos.merge(exactos[["id_ruta", "destino_exacto"]], on="id_ruta", how="left", validate="one_to_one")
    columnas = list(VARIABLES) + ["pendiente_media_abs_pct", "elevacion_max_m", "horas_marcha_efectiva_estimadas"]
    if datos[columnas].isna().any().any() or datos.destino_exacto.isna().any():
        raise ValueError("Hay datos faltantes en variables, esfuerzo o destino exacto")
    return datos


def escalar(datos: pd.DataFrame, variables=VARIABLES, pesos=None) -> np.ndarray:
    x = datos[list(variables)].to_numpy(float)
    if not np.isfinite(x).all() or np.any(x.std(axis=0) == 0):
        raise ValueError("Faltan datos o alguna variable es constante")
    x = (x - x.mean(axis=0)) / x.std(axis=0)  # ddof=0, igual que el modelo del 22/oct
    return x * np.asarray(pesos, float) if pesos is not None else x


# --------------------------------------------------------------- ajuste ----

def ordenar_grupos(etiquetas: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Reetiqueta 0..k-1 por la suma de coordenadas z del centroide (solo variables del modelo)."""
    grupos = np.unique(etiquetas)
    orden = sorted(grupos, key=lambda g: (float(x[etiquetas == g].sum(axis=1).mean()), int(g)))
    mapa = {g: i for i, g in enumerate(orden)}
    return np.asarray([mapa[g] for g in etiquetas], int)


def ajustar(datos: pd.DataFrame, k: int, variables=VARIABLES, pesos=None) -> dict:
    x = escalar(datos, variables, pesos)
    ajustes = []
    for semilla in SEMILLAS:
        modelo = KMeans(n_clusters=k, random_state=semilla, n_init=N_INIT, init="k-means++").fit(x)
        ajustes.append((float(modelo.inertia_), semilla, modelo.labels_.copy()))
    inercia, semilla, etiquetas = min(ajustes, key=lambda a: (a[0], a[1]))
    ordenadas = ordenar_grupos(etiquetas, x)
    ward = ordenar_grupos(fcluster(linkage(x, method="ward"), k, criterion="maxclust") - 1, x)
    return {
        "x": x, "etiquetas": ordenadas, "inercia": inercia, "semilla": semilla,
        "silueta": float(silhouette_score(x, ordenadas)),
        "ari_semillas": [float(adjusted_rand_score(etiquetas, a[2])) for a in ajustes],
        "inercias_semillas": [a[0] for a in ajustes],
        "tamanos_semillas": ["/".join(map(str, sorted(np.bincount(a[2])))) for a in ajustes],
        "ward": ward, "ari_ward": float(adjusted_rand_score(ordenadas, ward)),
    }


# ---------------------------------------------------------- escenarios ----

def _escenario(nombre: str, familia: str, sub: pd.DataFrame, base: pd.DataFrame, k: int = 3,
               variables=VARIABLES, pesos=None) -> dict:
    """Reajusta k-means y compara con la partición base solo en las rutas comunes."""
    try:
        modelo = ajustar(sub, k, variables, pesos)
    except Exception as error:  # se registra, no se oculta
        return {"escenario": nombre, "familia": familia, "n_rutas": len(sub), "fallo": f"{type(error).__name__}: {error}"}
    comunes = base.set_index("id_ruta").loc[sub.id_ruta, "grupo_k3"].to_numpy(int)
    ari_base = float(adjusted_rand_score(comunes, modelo["etiquetas"]))
    cambian = [r for r, b, c in zip(sub.id_ruta, comunes, modelo["etiquetas"]) if b != c]
    tam = np.bincount(modelo["etiquetas"], minlength=k)
    return {
        "escenario": nombre, "familia": familia, "n_rutas": len(sub), "fallo": "",
        "ari_con_base": round(ari_base, 4), "n_cambian_de_grupo": len(cambian),
        "rutas_cambian_de_grupo": "|".join(cambian), "tamanos_G1_G2_G3": "/".join(map(str, tam)),
        "silueta": round(modelo["silueta"], 4), "ari_semillas_min": round(min(modelo["ari_semillas"]), 4),
        "rutas_grupo_mas_pequeno": "|".join(sub.id_ruta[modelo["etiquetas"] == int(np.argmin(tam))]),
    }


def escenarios(datos: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for nombre, pesos in (("peso_distancia_x0.8", (0.8, 1)), ("peso_distancia_x1.25", (1.25, 1)),
                          ("peso_ascenso_x0.8", (1, 0.8)), ("peso_ascenso_x1.25", (1, 1.25))):
        filas.append(_escenario(nombre, "pesos_moderados", datos, base, pesos=pesos))
    for nombre, pesos in (("peso_distancia_x0.5", (0.5, 1)), ("peso_distancia_x2", (2, 1)),
                          ("peso_ascenso_x0.5", (1, 0.5)), ("peso_ascenso_x2", (1, 2))):
        filas.append(_escenario(nombre, "pesos_estres", datos, base, pesos=pesos))
    for nombre, columna in (("ascenso_mediana3", "ascenso_mediana3_m"), ("ascenso_mediana5", "ascenso_mediana5_m"),
                            ("ascenso_crudo", "ascenso_crudo_m")):
        sub = datos.copy()
        sub["ascenso_total_m"] = sub[columna]
        filas.append(_escenario(nombre, "filtrado_dem", sub, base))
    filas.append(_escenario("mas_pendiente_media", "variables_adicionales", datos, base,
                            variables=VARIABLES + ("pendiente_media_abs_pct",)))
    filas.append(_escenario("mas_elevacion_maxima", "variables_adicionales", datos, base,
                            variables=VARIABLES + ("elevacion_max_m",)))
    for ruta in datos.id_ruta:
        filas.append(_escenario(f"sin_{ruta}", "retirar_una", datos.loc[datos.id_ruta.ne(ruta)].reset_index(drop=True), base))
    filas.append(_escenario("sin_R026_R027", "retirar_varias",
                            datos.loc[~datos.id_ruta.isin(["R026", "R027"])].reset_index(drop=True), base))
    for criterio, columna in (("id_destino", "id_destino"), ("destino_exacto", "destino_exacto")):
        for etiqueta, ascendente in (("corta", True), ("larga", False)):
            sub = (datos.sort_values(["distancia_total_km", "id_ruta"], ascending=[ascendente, True])
                   .drop_duplicates(columna).sort_values("id_ruta").reset_index(drop=True))
            filas.append(_escenario(f"una_por_{criterio}_{etiqueta}", "una_por_destino", sub, base))
    return pd.DataFrame(filas)


def contraste_dbscan(datos: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    x = escalar(datos)
    k3 = base["grupo_k3"].to_numpy(int)
    filas = []
    for eps, min_samples in product((0.3, 0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5), (2, 3, 4)):
        etiquetas = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(x)
        retenidas = etiquetas != -1
        grupos = len(set(etiquetas) - {-1})
        ari_nr = (float(adjusted_rand_score(k3[retenidas], etiquetas[retenidas]))
                  if grupos >= 2 and retenidas.sum() >= 2 else np.nan)
        filas.append({
            "eps": eps, "min_samples": min_samples, "grupos_dbscan": grupos,
            "n_ruido": int((~retenidas).sum()), "cobertura": round(float(retenidas.mean()), 3),
            "rutas_ruido": "|".join(datos.id_ruta[~retenidas]),
            "ari_k3_solo_no_ruido": round(ari_nr, 4) if np.isfinite(ari_nr) else "",
            "ari_k3_ruido_como_grupo_20": round(float(adjusted_rand_score(k3, etiquetas)), 4),
            "aviso": "ARI solo no ruido NO es acuerdo sobre las 20 rutas",
        })
    return pd.DataFrame(filas)


# ------------------------------------------------------ descripción k=3 ----

def describir(datos: pd.DataFrame, etiquetas: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    medidas = {"distancia_km": datos.distancia_total_km, "ascenso_m": datos.ascenso_total_m,
               "esfuerzo_h": datos.horas_marcha_efectiva_estimadas}
    filas = []
    for g in range(3):
        fila = {"grupo": NOMBRES_GRUPO[g], "indice": g + 1, "n": int((etiquetas == g).sum()),
                "rutas": "|".join(datos.id_ruta[etiquetas == g])}
        for nombre, valores in medidas.items():
            v = valores[etiquetas == g]
            fila.update({f"{nombre}_min": round(v.min(), 3), f"{nombre}_mediana": round(v.median(), 3),
                         f"{nombre}_media": round(v.mean(), 3), f"{nombre}_max": round(v.max(), 3)})
        filas.append(fila)
    solapamientos, inversiones = [], []
    for g in range(2):
        for nombre, valores in medidas.items():
            inferior, superior = valores[etiquetas == g], valores[etiquetas == g + 1]
            solapa = inferior.max() > superior.min()
            solapamientos.append({"grupos_adyacentes": f"G{g + 1}-G{g + 2}", "medida": nombre,
                                  "max_inferior": round(inferior.max(), 3), "min_superior": round(superior.min(), 3),
                                  "se_solapan": "si" if solapa else "no"})
    h = datos.set_index("id_ruta").horas_marcha_efectiva_estimadas
    for gi in range(3):
        for gj in range(gi + 1, 3):
            for ri in datos.id_ruta[etiquetas == gi]:
                for rj in datos.id_ruta[etiquetas == gj]:
                    if h[ri] > h[rj]:
                        inversiones.append({"ruta_grupo_menor": ri, "grupo_menor": f"G{gi + 1}", "esfuerzo_h_menor": round(h[ri], 3),
                                            "ruta_grupo_mayor": rj, "grupo_mayor": f"G{gj + 1}", "esfuerzo_h_mayor": round(h[rj], 3),
                                            "adyacentes": "si" if gj - gi == 1 else "no"})
    return pd.DataFrame(filas), pd.DataFrame(solapamientos), pd.DataFrame(inversiones, columns=[
        "ruta_grupo_menor", "grupo_menor", "esfuerzo_h_menor", "ruta_grupo_mayor", "grupo_mayor", "esfuerzo_h_mayor", "adyacentes"])


def comparar_con_regla(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    matriz = pd.crosstab(base.grupo_k3_nombre, base.dificultad_regla).reindex(
        index=[NOMBRES_GRUPO[g] for g in range(3)], columns=["Fácil", "Moderada", "Difícil"], fill_value=0)
    discrepantes = base.loc[base.grupo_k3 + 1 != base.nivel_regla_orden].copy()
    discrepantes = discrepantes[["id_ruta", "id_destino", "distancia_total_km", "ascenso_total_m", "esfuerzo_estimado_h",
                                 "dificultad_regla", "grupo_k3_nombre", "silueta_individual_k3", "margen_relativo_k3"]]
    resumen = {
        "ari_k3_vs_regla": round(float(adjusted_rand_score(base.grupo_k3, base.nivel_regla_orden)), 4),
        "spearman_grupo_vs_esfuerzo_h": round(float(spearmanr(base.grupo_k3, base.esfuerzo_estimado_h).statistic), 4),
        "n_coinciden_por_orden": int((base.grupo_k3 + 1 == base.nivel_regla_orden).sum()),
        "n_discrepantes": int(len(discrepantes)),
        "aviso": "La regla vigente no es verdad de terreno: ARI y coincidencia son descriptivos, no exactitud",
    }
    return matriz.reset_index().rename(columns={"grupo_k3_nombre": "grupo_kmeans_k3"}), discrepantes, resumen


# ---------------------------------------------------------- criterios ----

def evaluar_criterios(metricas: pd.DataFrame, sens: pd.DataFrame, solap: pd.DataFrame,
                      inversiones: pd.DataFrame, tamanos: list[int]) -> tuple[pd.DataFrame, str]:
    k = metricas.set_index("k")
    c1 = float(k.loc[3, "ari_semillas_min"])
    s3, s2 = float(k.loc[3, "silueta"]), float(k.loc[2, "silueta"])
    adyacentes = inversiones[inversiones.adyacentes.eq("si")] if len(inversiones) else inversiones
    c4_inv, c4_sol = len(adyacentes), int(solap[(solap.medida == "esfuerzo_h") & solap.se_solapan.eq("si")].shape[0])

    def minimo(familia, nombres=None):
        f = sens[sens.familia.eq(familia) & sens.fallo.eq("")]
        if nombres:
            f = f[f.escenario.isin(nombres)]
        return float(f.ari_con_base.min()) if len(f) else float("nan")

    retiradas = sens[sens.familia.eq("retirar_una")]
    prop_ok = float((retiradas.ari_con_base >= 0.80).mean())
    filas = [
        ("C1 estabilidad entre semillas (ARI mín)", c1, ">= 0.95", c1 >= 0.95),
        ("C2a silueta k=3", s3, ">= 0.50", s3 >= 0.50),
        ("C2b silueta k=3 vs k=2 (diferencia)", s3 - s2, ">= -0.05", (s3 - s2) >= -0.05),
        ("C3 tamaño mínimo de grupo", min(tamanos), ">= 3", min(tamanos) >= 3),
        ("C4a inversiones de esfuerzo entre grupos adyacentes", c4_inv, "== 0", c4_inv == 0),
        ("C4b solapamiento de rangos de esfuerzo entre adyacentes", c4_sol, "== 0", c4_sol == 0),
        ("C5a pesos moderados (ARI mín)", minimo("pesos_moderados"), ">= 0.80", minimo("pesos_moderados") >= 0.80),
        ("C5b alternativas DEM mediana5 y crudo (ARI mín)", minimo("filtrado_dem", ["ascenso_mediana5", "ascenso_crudo"]), ">= 0.80",
         minimo("filtrado_dem", ["ascenso_mediana5", "ascenso_crudo"]) >= 0.80),
        ("C5c retiradas de una ruta con ARI >= 0.80 (proporción)", prop_ok, ">= 0.90", prop_ok >= 0.90),
        ("C5d una alternativa por destino (ARI mín)", minimo("una_por_destino"), ">= 0.80", minimo("una_por_destino") >= 0.80),
    ]
    tabla = pd.DataFrame([{"criterio": a, "valor": round(float(b), 4), "umbral": c, "cumple": "si" if d else "no"} for a, b, c, d in filas])
    grupos = {"C1": [0], "C2": [1, 2], "C3": [3], "C4": [4, 5], "C5": [6, 7, 8, 9]}
    fallan = [g for g, idx in grupos.items() if any(not filas[i][3] for i in idx)]
    decision = "A" if not fallan else ("B" if ("C4" in fallan or len(fallan) >= 2) else "C")
    tabla.loc[len(tabla)] = {"criterio": "Criterios que fallan", "valor": len(fallan), "umbral": "|".join(fallan), "cumple": ""}
    tabla.loc[len(tabla)] = {"criterio": "Decisión según reglas a priori", "valor": "", "umbral": decision, "cumple": ""}
    return tabla, decision


# ------------------------------------------------------------- principal ----

def ejecutar(fecha: str, salida: Path | None = None) -> dict:
    salida = salida or TABLAS
    datos = cargar()
    clas = _modulo("clasificar", "clasificar_dificultad_fisica.py")
    ajustes = {k: ajustar(datos, k) for k in K_EVALUADOS}
    ids = datos.id_ruta.tolist()
    metricas = pd.DataFrame([{
        "k": k, "n_rutas": len(datos), "variables": "|".join(VARIABLES), "escalado": "z-score ddof=0, pesos 1:1",
        "algoritmo": f"KMeans k-means++ n_init={N_INIT}, semillas 0-49, mínima inercia",
        "semilla_elegida": a["semilla"], "inercia": round(a["inercia"], 4), "silueta": round(a["silueta"], 4),
        "tamanos": "/".join(map(str, np.bincount(a["etiquetas"]))), "ari_semillas_min": round(min(a["ari_semillas"]), 4),
        "n_semillas_con_misma_particion": int(sum(v == 1.0 for v in a["ari_semillas"])), "ari_ward": round(a["ari_ward"], 4),
    } for k, a in ajustes.items()])
    semillas = pd.DataFrame([{"k": k, "semilla": s, "inercia": round(a["inercias_semillas"][i], 6),
                              "tamanos_grupos": a["tamanos_semillas"][i], "ari_con_ajuste_elegido": round(a["ari_semillas"][i], 4)}
                             for k, a in ajustes.items() for i, s in enumerate(SEMILLAS)])
    a3, x3 = ajustes[3], ajustes[3]["x"]
    etiquetas = a3["etiquetas"]
    centros_z = np.array([x3[etiquetas == g].mean(axis=0) for g in range(3)])
    distancias = np.sqrt(((x3[:, None, :] - centros_z[None, :, :]) ** 2).sum(axis=2))
    d_orden = np.sort(distancias, axis=1)
    base = datos[["id_ruta", "nombre_ruta", "id_destino", "destino_exacto", "distancia_total_km", "ascenso_total_m",
                  "pendiente_media_abs_pct", "elevacion_max_m"]].copy()
    base["esfuerzo_estimado_h"] = datos.horas_marcha_efectiva_estimadas.round(4)
    base["nivel_regla_orden"] = datos.nivel_orden.astype(int)
    base["dificultad_regla"] = datos.dificultad_fisica_estimada
    base["grupo_k2"] = ajustes[2]["etiquetas"] + 1
    base["grupo_k3"] = etiquetas
    base["grupo_k3_nombre"] = [NOMBRES_GRUPO[g] for g in etiquetas]
    base["grupo_ward_k3"] = a3["ward"] + 1
    base["silueta_individual_k3"] = silhouette_samples(x3, etiquetas).round(4)
    base["distancia_centroide_propio_z"] = distancias[np.arange(len(base)), etiquetas].round(4)
    base["distancia_segundo_centroide_z"] = [round(float(sorted(fila)[1]), 4) for fila in distancias]
    base["margen_relativo_k3"] = ((d_orden[:, 1] - d_orden[:, 0]) / np.maximum(d_orden[:, 0], 1e-12)).round(4)
    base["cerca_de_frontera"] = np.where((base.silueta_individual_k3 < UMBRAL_SILUETA_INDIVIDUAL) |
                                         (base.margen_relativo_k3 < UMBRAL_MARGEN_RELATIVO), "si", "no")
    base["ruta_a_revisar"] = np.where(base.id_ruta.isin(RUTAS_A_REVISAR), "si", "no")
    base = base.sort_values("id_ruta").reset_index(drop=True)
    base["grupo_k3"] = base["grupo_k3"].astype(int)
    describe, solap, inversiones = describir(datos, etiquetas)
    sens = escenarios(datos, base)
    dbscan = contraste_dbscan(datos, base)
    matriz, discrepantes, comp = comparar_con_regla(base)
    criterios, decision = evaluar_criterios(metricas, sens, solap, inversiones, list(np.bincount(etiquetas)))
    medias, desv = datos[list(VARIABLES)].to_numpy(float).mean(axis=0), datos[list(VARIABLES)].to_numpy(float).std(axis=0)
    centros_orig = np.array([datos.loc[etiquetas == g, list(VARIABLES)].to_numpy(float).mean(axis=0) for g in range(3)])
    centroides = pd.DataFrame([{
        "k": 3, "grupo": NOMBRES_GRUPO[g], "n": int((etiquetas == g).sum()),
        "centroide_distancia_z": round(centros_z[g, 0], 4), "centroide_ascenso_z": round(centros_z[g, 1], 4),
        "centroide_distancia_km": round(centros_orig[g, 0], 4), "centroide_ascenso_m": round(centros_orig[g, 1], 4),
    } for g in range(3)])
    for k in (2, 4):
        et = ajustes[k]["etiquetas"]
        for g in range(k):
            centroides.loc[len(centroides)] = {
                "k": k, "grupo": f"grupo {g + 1} de {k}", "n": int((et == g).sum()),
                "centroide_distancia_z": round(float(ajustes[k]["x"][et == g, 0].mean()), 4),
                "centroide_ascenso_z": round(float(ajustes[k]["x"][et == g, 1].mean()), 4),
                "centroide_distancia_km": round(float(datos.loc[et == g, VARIABLES[0]].mean()), 4),
                "centroide_ascenso_m": round(float(datos.loc[et == g, VARIABLES[1]].mean()), 4)}
    dataset_bytes = (TABLAS / "dataset_clasificacion_rutas.csv").read_bytes()
    parametros = {
        "version": "kmeans-k3-experimento-v1", "fecha": fecha, "estado": "contraste exploratorio; no sustituye la regla vigente",
        "variables": list(VARIABLES), "media_entrenamiento": medias.tolist(), "desviacion_entrenamiento": desv.tolist(),
        "centroides_estandarizados_k3": centros_z.tolist(), "orden_grupos": "suma de coordenadas z del centroide, ascendente",
        "nombres_grupo": [NOMBRES_GRUPO[g] for g in range(3)], "n_init": N_INIT, "semillas": [SEMILLAS[0], SEMILLAS[-1]],
        "semilla_elegida_k3": a3["semilla"], "ids_entrenamiento": ids,
        "correlacion_distancia_ascenso": {"pearson": round(float(datos[list(VARIABLES)].corr().iloc[0, 1]), 4),
                                          "spearman": round(float(datos[list(VARIABLES)].corr("spearman").iloc[0, 1]), 4)},
        "rango_entrenamiento": {v: [float(datos[v].min()), float(datos[v].max())] for v in VARIABLES},
        "sha256_dataset": hashlib.sha256(dataset_bytes).hexdigest(),
        "versiones": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                      "scipy": scipy.__version__, "scikit-learn": sklearn.__version__},
        "comparacion_con_regla": comp, "decision_reglas_a_priori": decision,
        "limite": "Grupos relativos a la muestra; no predicen seguridad, acceso, técnica, clima ni aptitud personal",
    }
    salidas = {
        "metricas": metricas, "semillas": semillas, "asignaciones": base, "centroides": centroides,
        "grupos_descripcion": describe, "solapamientos": solap, "inversiones": inversiones, "sensibilidad": sens,
        "dbscan": dbscan, "comparacion_regla_matriz": matriz, "comparacion_regla_discrepancias": discrepantes,
        "criterios": criterios,
    }
    for nombre, tabla in salidas.items():
        tabla.to_csv(salida / f"kmeans_k3_{nombre}_{fecha}.csv", index=False, encoding="utf-8")
    (salida / f"kmeans_k3_parametros_{fecha}.json").write_text(json.dumps(parametros, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"datos": datos, "salidas": salidas, "parametros": parametros, "decision": decision}


def asignar_nueva_ruta(distancia_total_km: float, ascenso_total_m: float, parametros: dict) -> dict:
    """Grupo k=3 por centroide más cercano; marca extrapolación fuera del rango de entrenamiento."""
    valores = np.array([distancia_total_km, ascenso_total_m], float)
    if not np.isfinite(valores).all() or np.any(valores < 0):
        raise ValueError("Distancia o ascenso no válido")
    z = (valores - np.array(parametros["media_entrenamiento"])) / np.array(parametros["desviacion_entrenamiento"])
    distancias = np.sqrt(((np.array(parametros["centroides_estandarizados_k3"]) - z) ** 2).sum(axis=1))
    rango = parametros["rango_entrenamiento"]
    fuera = not (rango[VARIABLES[0]][0] <= valores[0] <= rango[VARIABLES[0]][1]
                 and rango[VARIABLES[1]][0] <= valores[1] <= rango[VARIABLES[1]][1])
    return {"grupo_indice": int(np.argmin(distancias)) + 1, "grupo": parametros["nombres_grupo"][int(np.argmin(distancias))],
            "extrapolacion": fuera}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", required=True)
    args = parser.parse_args()
    resultado = ejecutar(date.fromisoformat(args.fecha).isoformat())
    s = resultado["salidas"]
    print(s["metricas"].to_string(index=False))
    print(s["grupos_descripcion"].to_string(index=False))
    print(s["criterios"].to_string(index=False))
    print("Decisión según reglas a priori:", resultado["decision"])


if __name__ == "__main__":
    main()
