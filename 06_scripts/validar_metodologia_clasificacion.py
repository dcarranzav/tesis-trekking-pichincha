"""Validación metodológica reproducible de la agrupación exploratoria de rutas.

Uso: python 06_scripts/validar_metodologia_clasificacion.py --fecha 2026-10-22

Lee solo ``dataset_clasificacion_rutas.csv`` y ``solapamiento_rutas_*.csv`` (si existe).
Escribe tablas, figuras y un informe nuevos con la fecha de ejecución. NO escribe
``niveles_esfuerzo_finales.csv`` ni ``validacion_modelo_final.json`` y no habilita
recomendaciones: la decisión de publicación es separada y humana.

Los criterios de "grupos defendibles" se explicitan AQUÍ antes de ejecutar
esta evaluación. No son una preregistración independiente: ya existían
ensayos exploratorios sobre estas rutas.
"""

from argparse import ArgumentParser
from datetime import date
from itertools import combinations
import json
import os
from pathlib import Path
import sys

if sys.platform == "win32":
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parents[1]
TABLAS = RAIZ / "07_resultados/tablas"
FIGURAS = RAIZ / "07_resultados/figuras"
DOC = RAIZ / "01_documentacion"
ENTRADA = TABLAS / "dataset_clasificacion_rutas.csv"

VARIABLES = ["distancia_total_km", "ascenso_total_m", "elevacion_max_m", "pendiente_media_abs_pct"]
VARIABLE_P95 = "pendiente_p95_abs_pct"
SEMILLAS = range(50)
N_INIT = 10
EPS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
MIN_SAMPLES = (2, 3, 4)
GRUPO_MINORITARIO_ESPERADO = {"R001", "R003", "R006", "R022"}  # solo para comprobarlo, no para fijarlo
# Umbrales explícitos de esta evaluación (ver docstring)
CRITERIOS = {
    "ari_semillas_min": 0.90,
    "ari_ward": 0.90,
    "ari_loo_min": 0.70,
    "tamano_minimo_grupo": 3,
    "silueta_minima": 0.40,
    "ari_sensibilidad_min": 0.70,
}


def cargar() -> pd.DataFrame:
    datos = pd.read_csv(ENTRADA)
    assert datos["id_ruta"].is_unique, "ID de ruta duplicados"
    e = datos.loc[datos["estado_modelado"].eq("elegible_actual")].copy()
    cols = VARIABLES + [VARIABLE_P95]
    for c in cols:
        e[c] = pd.to_numeric(e[c], errors="coerce")
    assert np.isfinite(e[cols].to_numpy()).all(), "Valores faltantes o no finitos"
    assert (e[cols].nunique() > 1).all(), "Variable constante"
    return e.sort_values("id_ruta").reset_index(drop=True)


def escalar(datos, variables, pesos=None):
    x = StandardScaler().fit_transform(datos[variables])
    if pesos:
        for i, v in enumerate(variables):
            x[:, i] *= pesos.get(v, 1.0)
    return x


def kmeans_mejor(x, k):
    """Mejor partición (menor inercia) entre semillas, más todas las particiones."""
    ajustes = [KMeans(k, random_state=s, n_init=N_INIT).fit(x) for s in SEMILLAS]
    mejor = min(ajustes, key=lambda a: a.inertia_)
    return mejor, ajustes


def reetiquetar(etiquetas, ascenso):
    """Ordena grupos por ascenso medio creciente (solo para comparar; el orden no es una clase)."""
    etiquetas = np.asarray(etiquetas)
    orden = sorted(np.unique(etiquetas), key=lambda g: float(np.mean(ascenso[etiquetas == g])))
    mapa = {g: i for i, g in enumerate(orden)}
    return np.array([mapa[g] for g in etiquetas])


def ari_comun(ids_a, lab_a, ids_b, lab_b):
    a, b = dict(zip(ids_a, lab_a)), dict(zip(ids_b, lab_b))
    comun = sorted(set(a) & set(b))
    return float(adjusted_rand_score([a[i] for i in comun], [b[i] for i in comun])), len(comun)


def particion(datos, variables, k, pesos=None):
    x = escalar(datos, variables, pesos)
    mejor, ajustes = kmeans_mejor(x, k)
    lab = reetiquetar(mejor.labels_, datos["ascenso_total_m"].to_numpy())
    return x, mejor, ajustes, lab


# ---------------------------------------------------------------- bloques
def bloque_reproduccion(e):
    """Contrasta con el ensayo previo r027 sin aceptar cifras solo por estar en un informe."""
    filas = []
    previo = sorted(TABLAS.glob("evaluacion_clustering_exploratorio_sklearn_*_r027.csv"))
    if not previo:
        return pd.DataFrame(), "sin ensayo previo r027 para contrastar"
    antes = pd.read_csv(previo[-1])
    antes = antes[antes["escenario"].eq("base_4_variables")]
    grupos_prev = sorted(TABLAS.glob("grupos_exploratorios_sklearn_*_r027.csv"))
    gp = pd.read_csv(grupos_prev[-1]) if grupos_prev else pd.DataFrame()
    for k in (2, 3, 4):
        x = escalar(e, VARIABLES)
        mejor, aj = kmeans_mejor(x, k)
        ari_prev = np.nan
        if len(gp):
            s = gp[(gp.escenario == "base_4_variables") & (gp.k == k)].set_index("id_ruta")
            ari_prev = adjusted_rand_score(s.loc[e.id_ruta, "grupo_numerico_sin_orden"], mejor.labels_)
        ref = antes[antes.k == k].iloc[0]
        filas.append({
            "k": k,
            "silueta_nueva": round(silhouette_score(x, mejor.labels_), 4),
            "silueta_previa": ref.silueta,
            "inercia_nueva": round(float(mejor.inertia_), 4),
            "inercia_previa": ref.inercia,
            "ari_asignacion_vs_previa": round(float(ari_prev), 4),
            "coincide": bool(abs(silhouette_score(x, mejor.labels_) - ref.silueta) < 1e-3
                             and abs(mejor.inertia_ - ref.inercia) < 1e-3),
        })
    return pd.DataFrame(filas), ""


def bloque_integridad(e):
    x = escalar(e, VARIABLES)
    return {
        "n_rutas": int(len(e)),
        "ids_unicos": bool(e["id_ruta"].is_unique),
        "valores_faltantes": int(e[VARIABLES + [VARIABLE_P95]].isna().sum().sum()),
        "media_estandarizada_max_abs": float(np.abs(x.mean(axis=0)).max()),
        "desv_estandarizada_min_max": [float(x.std(axis=0).min()), float(x.std(axis=0).max())],
        "destinos_distintos": int(e["id_destino"].nunique()),
        "rutas_por_destino": e.groupby("id_destino")["id_ruta"].apply(list).to_dict(),
    }


def bloque_kmeans(e):
    resumen, semillas, centroides, asign = [], [], [], []
    for k in (2, 3, 4):
        x, mejor, ajustes, lab = particion(e, VARIABLES, k)
        ward = AgglomerativeClustering(k, linkage="ward").fit_predict(x)
        sils = [silhouette_score(x, a.labels_) for a in ajustes]
        aris = [adjusted_rand_score(mejor.labels_, a.labels_) for a in ajustes]
        pares = [adjusted_rand_score(a.labels_, b.labels_) for a, b in combinations(ajustes[:15], 2)]
        tam = np.bincount(lab)
        resumen.append({
            "k": k, "silueta_mejor": round(silhouette_score(x, mejor.labels_), 4),
            "silueta_semillas_min": round(min(sils), 4), "silueta_semillas_max": round(max(sils), 4),
            "inercia_mejor": round(float(mejor.inertia_), 4),
            "tamanos": "/".join(map(str, sorted(tam))),
            "tamano_minimo": int(tam.min()),
            "ari_semillas_min": round(min(aris), 4), "ari_semillas_media": round(float(np.mean(aris)), 4),
            "ari_entre_pares_min": round(min(pares), 4),
            "semillas_que_reproducen_mejor": f"{sum(a == 1 for a in np.round(aris, 6))}/{len(aris)}",
            "ari_ward": round(float(adjusted_rand_score(lab, reetiquetar(ward, e['ascenso_total_m'].to_numpy()))), 4),
        })
        for s, a, sil in zip(SEMILLAS, ajustes, sils):
            semillas.append({"k": k, "semilla": s, "silueta": round(sil, 4),
                             "inercia": round(float(a.inertia_), 4),
                             "ari_vs_mejor": round(float(adjusted_rand_score(mejor.labels_, a.labels_)), 4)})
        for g in range(k):
            m = e.loc[lab == g]
            fila = {"k": k, "grupo_ordenado_por_ascenso": g, "n": int(len(m)), "rutas": "|".join(m.id_ruta)}
            for v in VARIABLES + [VARIABLE_P95]:
                fila[f"{v}_media"] = round(float(m[v].mean()), 2)
                fila[f"{v}_mediana"] = round(float(m[v].median()), 2)
                fila[f"{v}_min"] = round(float(m[v].min()), 2)
                fila[f"{v}_max"] = round(float(m[v].max()), 2)
            centroides.append(fila)
        for i, r in enumerate(e.id_ruta):
            asign.append({"k": k, "id_ruta": r, "id_destino": e.id_destino[i],
                          "grupo_ordenado_por_ascenso": int(lab[i]),
                          "grupo_ward_ordenado": int(reetiquetar(ward, e['ascenso_total_m'].to_numpy())[i])})
    return pd.DataFrame(resumen), pd.DataFrame(semillas), pd.DataFrame(centroides), pd.DataFrame(asign)


def bloque_origen_k2(e):
    """¿Qué variable explica la partición k=2? (ARI de la partición en 1-D vs la de 4 variables)"""
    _, _, _, lab = particion(e, VARIABLES, 2)
    filas = []
    for v in VARIABLES + [VARIABLE_P95]:
        x1 = StandardScaler().fit_transform(e[[v]])
        l1 = KMeans(2, random_state=0, n_init=N_INIT).fit(x1).labels_
        filas.append({"variable_sola": v, "ari_vs_k2_base": round(float(adjusted_rand_score(lab, l1)), 4),
                      "silueta_1d": round(float(silhouette_score(x1, l1)), 4)})
    # Contraste convergente a priori (sin etiquetas turísticas): regla de Naismith, h = km/5 + m/600.
    e = e.assign(indice_naismith_h=e["distancia_total_km"] / 5 + e["ascenso_total_m"] / 600)
    xn = StandardScaler().fit_transform(e[["indice_naismith_h"]])
    ln = KMeans(2, random_state=0, n_init=N_INIT).fit(xn).labels_
    filas.append({"variable_sola": "indice_naismith_h (referencia a priori)",
                  "ari_vs_k2_base": round(float(adjusted_rand_score(lab, ln)), 4),
                  "silueta_1d": round(float(silhouette_score(xn, ln)), 4)})
    g1 = e.loc[lab == 1]
    g0 = e.loc[lab == 0]
    sep = []
    for v in VARIABLES + [VARIABLE_P95]:
        sep.append({"variable": v, "minimo_grupo_mayor": round(float(g1[v].min()), 2),
                    "maximo_grupo_menor": round(float(g0[v].max()), 2),
                    "separacion_total": bool(g1[v].min() > g0[v].max())})
    sep.append({"variable": "indice_naismith_h", "minimo_grupo_mayor": round(float(g1["indice_naismith_h"].min()), 2),
                "maximo_grupo_menor": round(float(g0["indice_naismith_h"].max()), 2),
                "separacion_total": bool(g1["indice_naismith_h"].min() > g0["indice_naismith_h"].max())})
    # rutas extremas: puntuaciones z
    z = pd.DataFrame(StandardScaler().fit_transform(e[VARIABLES]), columns=VARIABLES, index=e.id_ruta).round(2)
    return pd.DataFrame(filas), pd.DataFrame(sep), z, set(g1.id_ruta)


def bloque_loo(e):
    """Retira cada ruta y rehace k=2/3; ARI sobre las rutas comunes (¿unas pocas rutas extremas mandan?)."""
    filas = []
    for k in (2, 3):
        _, _, _, base = particion(e, VARIABLES, k)
        for i, r in enumerate(e.id_ruta):
            sub = e.drop(index=i).reset_index(drop=True)
            _, _, _, lab = particion(sub, VARIABLES, k)
            a, n = ari_comun(e.id_ruta, base, sub.id_ruta, lab)
            filas.append({"k": k, "ruta_retirada": r, "ari_vs_base": round(a, 4), "n_comun": n})
    return pd.DataFrame(filas)


def solapadas(e):
    f = sorted(TABLAS.glob("solapamiento_rutas_*.csv"))
    if not f:
        return []
    s = pd.read_csv(f[-1])
    ids = set(e.id_ruta)
    s = s[s.id_ruta_a.isin(ids) & s.id_ruta_b.isin(ids)]
    s = s[(s.fraccion_a_cubierta_20m >= 0.5) | (s.fraccion_b_cubierta_20m >= 0.5)]
    return [(a, b) for a, b in zip(s.id_ruta_a, s.id_ruta_b)]


def bloque_sensibilidad(e):
    filas = []
    ids_base = {}
    for k in (2, 3):
        _, _, _, base = particion(e, VARIABLES, k)
        ids_base[k] = base
    espec = [("base", e, VARIABLES, None)]
    espec += [
        ("sin_distancia", e, [v for v in VARIABLES if v != "distancia_total_km"], None),
        ("sin_ascenso", e, [v for v in VARIABLES if v != "ascenso_total_m"], None),
        ("sin_altitud_maxima", e, [v for v in VARIABLES if v != "elevacion_max_m"], None),
        ("altitud_peso_0.5", e, VARIABLES, {"elevacion_max_m": 0.5}),
        ("altitud_peso_2", e, VARIABLES, {"elevacion_max_m": 2.0}),
        ("con_pendiente_p95", e, VARIABLES + [VARIABLE_P95], None),
        ("sin_R026", e[e.id_ruta != "R026"], VARIABLES, None),
        ("sin_R027", e[e.id_ruta != "R027"], VARIABLES, None),
        ("sin_R026_ni_R027", e[~e.id_ruta.isin(["R026", "R027"])], VARIABLES, None),
        ("sin_R011_R013_por_confirmar", e[~e.id_ruta.isin(["R011", "R013"])], VARIABLES, None),
    ]
    sol = solapadas(e)
    if sol:
        quitar = {b for _, b in sol}
        espec.append(("sin_rutas_muy_solapadas(" + ",".join(sorted(quitar)) + ")", e[~e.id_ruta.isin(quitar)], VARIABLES, None))
    # una alternativa por destino (extremos deterministas: la más larga / la más corta)
    for etiqueta, idx in (("una_por_destino_mas_larga", e.groupby("id_destino")["distancia_total_km"].idxmax()),
                          ("una_por_destino_mas_corta", e.groupby("id_destino")["distancia_total_km"].idxmin())):
        espec.append((etiqueta, e.loc[idx].sort_values("id_ruta"), VARIABLES, None))
    for nombre, datos, vars_, pesos in espec:
        datos = datos.reset_index(drop=True)
        for k in (2, 3):
            x, mejor, ajustes, lab = particion(datos, vars_, k, pesos)
            a, n = ari_comun(e.id_ruta, ids_base[k], datos.id_ruta, lab)
            mayor = "|".join(datos.id_ruta[lab == lab.max()]) if k == 2 else ""
            filas.append({
                "escenario": nombre, "k": k, "n_rutas": len(datos), "variables": "|".join(vars_),
                "silueta": round(silhouette_score(x, mejor.labels_), 4),
                "tamanos": "/".join(map(str, sorted(np.bincount(lab)))),
                "ari_vs_base_en_comunes": round(a, 4), "n_comunes": n,
                "ari_semillas_min": round(min(adjusted_rand_score(mejor.labels_, aa.labels_) for aa in ajustes), 4),
                "grupo_mayor_ascenso_k2": mayor,
            })
    return pd.DataFrame(filas)


def bloque_dbscan(e):
    x = escalar(e, VARIABLES)
    _, _, _, lab2 = particion(e, VARIABLES, 2)
    _, _, _, lab3 = particion(e, VARIABLES, 3)
    metr, comp, asign = [], [], []
    for ms in MIN_SAMPLES:
        for eps in EPS:
            lab = DBSCAN(eps=eps, min_samples=ms).fit_predict(x)
            ok = lab != -1
            ng = len(set(lab[ok]))
            ruido = list(e.id_ruta[~ok])
            # estabilidad: retirar cada ruta y comparar en rutas no ruido en ambas
            aris = []
            for i in range(len(e)):
                idx = [j for j in range(len(e)) if j != i]
                lab_i = DBSCAN(eps=eps, min_samples=ms).fit_predict(StandardScaler().fit_transform(e.iloc[idx][VARIABLES]))
                a_ids = [e.id_ruta[j] for j in idx]
                da, db = dict(zip(e.id_ruta, lab)), dict(zip(a_ids, lab_i))
                comun = [r for r in a_ids if da[r] != -1 and db[r] != -1]
                if len(comun) >= 3 and len(set(da[r] for r in comun)) + len(set(db[r] for r in comun)) > 2:
                    aris.append(adjusted_rand_score([da[r] for r in comun], [db[r] for r in comun]))
                elif len(comun) >= 3:
                    aris.append(1.0)
            ruido_loo = []
            sil = silhouette_score(x[ok], lab[ok]) if ng >= 2 and ok.sum() > ng else np.nan
            metr.append({
                "eps": eps, "min_samples": ms, "n_grupos": ng, "n_ruido": int((~ok).sum()),
                "cobertura_pct": round(100 * float(ok.mean()), 1),
                "tamanos_grupos": "/".join(map(str, sorted(np.bincount(lab[ok]))) ) if ok.any() else "",
                "silueta_sin_ruido": round(float(sil), 4) if np.isfinite(sil) else np.nan,
                "ari_estabilidad_loo_min": round(min(aris), 4) if aris else np.nan,
                "rutas_ruido": "|".join(ruido),
                "ruido_incluye_R001_R003_R006_R022": GRUPO_MINORITARIO_ESPERADO <= set(ruido),
            })
            for kk, base in ((2, lab2), (3, lab3)):
                # ARI solo es informativo si ambas particiones tienen >= 2 grupos entre las rutas no ruido
                if ok.sum() >= 3 and ng >= 2 and len(set(base[ok])) >= 2:
                    a = adjusted_rand_score(base[ok], lab[ok])
                else:
                    a = np.nan
                comp.append({"eps": eps, "min_samples": ms, "k_kmeans": kk, "n_grupos_dbscan": ng,
                             "rutas_comparadas": int(ok.sum()), "rutas_fuera_por_ruido": int((~ok).sum()),
                             "ari_solo_no_ruido": round(float(a), 4) if np.isfinite(a) else np.nan,
                             "kmeans_grupos_en_no_ruido": len(set(base[ok])),
                             "comparable": bool(np.isfinite(a))})
            for r, l in zip(e.id_ruta, lab):
                asign.append({"eps": eps, "min_samples": ms, "id_ruta": r, "grupo_dbscan": int(l)})
    return pd.DataFrame(metr), pd.DataFrame(comp), pd.DataFrame(asign)


# ---------------------------------------------------------------- decisión
def evaluar_criterios(res_k, loo, sens, dbs):
    k2 = res_k[res_k.k == 2].iloc[0]
    l2 = loo[loo.k == 2]
    s2 = sens[(sens.k == 2) & (sens.escenario != "base")]
    # sensibilidad: se juzga por las variantes que conservan las mismas variables (rutas retiradas,
    # pesos y destino único); las variantes que cambian el conjunto de variables se reportan aparte.
    cambian_vars = {"sin_distancia", "sin_ascenso", "sin_altitud_maxima", "con_pendiente_p95"}
    s_rutas = s2[~s2.escenario.isin(cambian_vars)]
    s_vars = s2[s2.escenario.isin(cambian_vars)]
    filas = [
        ("C1 estabilidad entre semillas (ARI mín)", float(k2.ari_semillas_min), f">= {CRITERIOS['ari_semillas_min']}", k2.ari_semillas_min >= CRITERIOS["ari_semillas_min"]),
        ("C2 concordancia con Ward (ARI)", float(k2.ari_ward), f">= {CRITERIOS['ari_ward']}", k2.ari_ward >= CRITERIOS["ari_ward"]),
        ("C3 estabilidad al retirar una ruta (ARI mín)", float(l2.ari_vs_base.min()), f">= {CRITERIOS['ari_loo_min']}", l2.ari_vs_base.min() >= CRITERIOS["ari_loo_min"]),
        ("C4 tamaño mínimo de grupo", int(k2.tamano_minimo), f">= {CRITERIOS['tamano_minimo_grupo']}", k2.tamano_minimo >= CRITERIOS["tamano_minimo_grupo"]),
        ("C5 silueta k=2", float(k2.silueta_mejor), f">= {CRITERIOS['silueta_minima']}", k2.silueta_mejor >= CRITERIOS["silueta_minima"]),
        ("C6 sensibilidad a rutas/pesos/destinos (ARI mín en comunes)", float(s_rutas.ari_vs_base_en_comunes.min()), f">= {CRITERIOS['ari_sensibilidad_min']}", s_rutas.ari_vs_base_en_comunes.min() >= CRITERIOS["ari_sensibilidad_min"]),
        ("C7 sensibilidad a cambio de variables (ARI mín en comunes)", float(s_vars.ari_vs_base_en_comunes.min()), f">= {CRITERIOS['ari_sensibilidad_min']}", s_vars.ari_vs_base_en_comunes.min() >= CRITERIOS["ari_sensibilidad_min"]),
    ]
    return pd.DataFrame(filas, columns=["criterio", "valor", "umbral_previo", "cumple"])


# ---------------------------------------------------------------- figuras
def figuras(e, lab2, lab3, dbs, fecha):
    FIGURAS.mkdir(parents=True, exist_ok=True)
    col = {0: "#3b7ea1", 1: "#d1603d"}
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
    pares = [("distancia_total_km", "ascenso_total_m"), ("elevacion_max_m", "ascenso_total_m"),
             ("distancia_total_km", "pendiente_media_abs_pct")]
    for a, (vx, vy) in zip(ax, pares):
        for g in (0, 1):
            m = lab2 == g
            a.scatter(e.loc[m, vx], e.loc[m, vy], c=col[g], s=46, label=f"grupo {g} (n={m.sum()})")
        for r, xx, yy in zip(e.id_ruta, e[vx], e[vy]):
            a.annotate(r, (xx, yy), fontsize=7, xytext=(3, 3), textcoords="offset points")
        a.set_xlabel(vx); a.set_ylabel(vy); a.grid(alpha=.25)
    ax[0].legend(title="K-means k=2\n(orden por ascenso)", fontsize=8)
    fig.suptitle("Partición exploratoria k=2 en unidades originales — no es una clase de esfuerzo publicada")
    fig.tight_layout(); fig.savefig(FIGURAS / f"validacion_k2_unidades_originales_{fecha}.png", dpi=140); plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(15, 3.8))
    for a, ms in zip(ax, MIN_SAMPLES):
        s = dbs[dbs.min_samples == ms]
        a.bar([str(x) for x in s.eps], s.n_ruido, color="#888")
        for i, (ng, nr) in enumerate(zip(s.n_grupos, s.n_ruido)):
            a.text(i, nr + .2, f"{ng}g", ha="center", fontsize=8)
        a.set_title(f"DBSCAN min_samples={ms}"); a.set_xlabel("eps"); a.set_ylabel("rutas ruido (-1)")
        a.set_ylim(0, len(e))
    fig.suptitle("DBSCAN como contraste: rutas ruido y número de grupos (g) por configuración")
    fig.tight_layout(); fig.savefig(FIGURAS / f"validacion_dbscan_ruido_{fecha}.png", dpi=140); plt.close(fig)


def main():
    p = ArgumentParser(description=__doc__)
    p.add_argument("--fecha", required=True)
    f = date.fromisoformat(p.parse_args().fecha).isoformat()
    e = cargar()
    integridad = bloque_integridad(e)
    repro, aviso = bloque_reproduccion(e)
    res_k, semillas, cent, asign = bloque_kmeans(e)
    origen, separacion, z, minor = bloque_origen_k2(e)
    loo = bloque_loo(e)
    sens = bloque_sensibilidad(e)
    dbs, comp, asig_db = bloque_dbscan(e)
    crit = evaluar_criterios(res_k, loo, sens, dbs)
    _, _, _, lab2 = particion(e, VARIABLES, 2)
    _, _, _, lab3 = particion(e, VARIABLES, 3)
    figuras(e, lab2, lab3, dbs, f)
    salidas = {
        "reproduccion_previa": repro, "kmeans_resumen": res_k, "kmeans_semillas": semillas,
        "centroides_unidades_originales": cent, "asignaciones": asign, "origen_k2_variable_sola": origen,
        "separacion_k2_por_variable": separacion, "puntuaciones_z": z.reset_index(),
        "estabilidad_retirando_una_ruta": loo, "sensibilidad": sens,
        "dbscan_malla": dbs, "dbscan_vs_kmeans": comp, "dbscan_asignaciones": asig_db,
        "criterios_decision": crit,
    }
    for nombre, tabla in salidas.items():
        tabla.to_csv(TABLAS / f"validacion_{nombre}_{f}.csv", index=False, encoding="utf-8")
    resumen = {
        "fecha": f, "integridad": integridad, "criterios_previos": CRITERIOS,
        "grupo_mayor_ascenso_k2": sorted(minor),
        "dbscan_multigrupo_ruido_incluye_las_cuatro": {
            "configuraciones_con_2_o_mas_grupos": int((dbs.n_grupos >= 2).sum()),
            "de_ellas_con_R001_R003_R006_R022_como_ruido": int(((dbs.n_grupos >= 2) & dbs.ruido_incluye_R001_R003_R006_R022).sum())},
        "grupo_mayor_coincide_con_R001_R003_R006_R022": minor == GRUPO_MINORITARIO_ESPERADO,
        "criterios_cumplidos": int(crit.cumple.sum()), "criterios_totales": int(len(crit)),
        "versiones": {"pandas": pd.__version__, "numpy": np.__version__,
                      "sklearn": __import__("sklearn").__version__},
        "parametros": {"semillas": [SEMILLAS.start, SEMILLAS.stop - 1], "n_init": N_INIT,
                       "eps": list(EPS), "min_samples": list(MIN_SAMPLES), "variables": VARIABLES},
        "aviso": aviso,
        "habilitacion": "NO: este resumen no es validacion_modelo_final.json ni habilita recomendaciones",
    }
    (TABLAS / f"validacion_resumen_{f}.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    for n in ("reproduccion_previa", "kmeans_resumen", "origen_k2_variable_sola", "separacion_k2_por_variable",
              "criterios_decision"):
        print("\n##", n); print(salidas[n].to_string(index=False))
    print("\n## sensibilidad k=2"); print(sens[sens.k == 2].drop(columns=["variables"]).to_string(index=False))
    print("\n## loo k=2 min", loo[loo.k == 2].ari_vs_base.min()); print(loo[loo.ari_vs_base < 1].to_string(index=False))
    print("\n## dbscan"); print(dbs.drop(columns=["ruido_incluye_R001_R003_R006_R022"]).to_string(index=False))
    print(comp[comp.n_grupos_dbscan >= 1].to_string(index=False))
    print(json.dumps(resumen["integridad"], ensure_ascii=False, default=str)[:600])


if __name__ == "__main__":
    main()
