"""Indicador continuo de esfuerzo de referencia a partir de distancia y ascenso.

Uso: python 06_scripts/calcular_indicador_esfuerzo.py --fecha 2026-10-22

Definición (explícita, sin etiquetas turísticas ni ajuste a los datos):

    HEN = distancia_total_km / V + ascenso_total_m / R      con V = 5 km/h y R = 600 m/h

Es la regla de Naismith: horas-equivalentes de esfuerzo de REFERENCIA. No es un tiempo
medido ni un tiempo de marcha pronosticado para una persona, y no incluye pausas, carga,
estado del sendero, altitud, clima ni técnica. La altitud (``elevacion_max_m``) se conserva
como columna de advertencia SEPARADA y no entra en el indicador. El script no crea clases
(«fácil/difícil»), no escribe ``niveles_esfuerzo_finales.csv`` ni ``validacion_modelo_final.json``
y no habilita recomendaciones.
"""

from argparse import ArgumentParser
from datetime import date
import importlib.util
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
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parents[1]
TABLAS = RAIZ / "07_resultados/tablas"
FIGURAS = RAIZ / "07_resultados/figuras"
PERFILES = RAIZ / "04_datos_procesados/perfiles"
PERFILES_RAW = RAIZ / "03_datos_intermedios/elevacion"

V_KMH = 5.0
R_M_H = 600.0
REJILLA_V = (4.0, 4.5, 5.0, 5.5)
REJILLA_R = (300.0, 400.0, 500.0, 600.0, 800.0)
SIGMAS_DEM_M = (1.0, 2.0, 4.0)
N_SIMULACIONES = 500
SEMILLA = 20261022


# ------------------------------------------------------------------ definición
def horas_equivalentes(distancia_km, ascenso_m, v=V_KMH, r=R_M_H):
    """Regla de Naismith. Solo depende de distancia y ascenso."""
    return np.asarray(distancia_km, float) / v + np.asarray(ascenso_m, float) / r


def rangos(valores):
    """1 = mayor esfuerzo. Empates con el promedio de posiciones."""
    return pd.Series(np.asarray(valores, float)).rank(ascending=False, method="average").to_numpy()


def spearman(a, b):
    return float(pd.Series(a).corr(pd.Series(b), method="spearman"))


def mediana_centrada(valores, ventana):
    """Misma mediana centrada del procesamiento de elevación (extremos conservados)."""
    radio = ventana // 2
    salida = np.array([np.median(valores[max(0, i - radio): i + radio + 1]) for i in range(len(valores))], float)
    salida[0], salida[-1] = valores[0], valores[-1]
    return salida


def ascenso_total(elevacion, tipo):
    cambio = np.diff(elevacion)
    subida, bajada = cambio[cambio > 0].sum(), -cambio[cambio < 0].sum()
    return float(subida + bajada) if tipo == "ida_y_vuelta" else float(subida)


def tobler_horas(distancia_m, elevacion, tipo):
    """Función de marcha de Tobler sobre el perfil (solo contraste secundario)."""
    def sentido(d, z):
        pendiente = np.diff(z) / np.diff(d)
        velocidad = 6.0 * np.exp(-3.5 * np.abs(pendiente + 0.05))  # km/h
        return float((np.diff(d) / 1000.0 / velocidad).sum())
    ida = sentido(distancia_m, elevacion)
    if tipo == "ida_y_vuelta":
        return ida + sentido(distancia_m[-1] - distancia_m[::-1], elevacion[::-1])
    return ida


# ------------------------------------------------------------------ datos
def cargar():
    datos = pd.read_csv(TABLAS / "dataset_clasificacion_rutas.csv")
    assert datos["id_ruta"].is_unique
    e = datos.loc[datos["estado_modelado"].eq("elegible_actual")].sort_values("id_ruta").reset_index(drop=True)
    for c in ("distancia_total_km", "ascenso_total_m", "elevacion_max_m"):
        e[c] = pd.to_numeric(e[c], errors="coerce")
    assert np.isfinite(e[["distancia_total_km", "ascenso_total_m", "elevacion_max_m"]].to_numpy()).all()
    return e


def perfiles(e):
    """Perfiles procesados y crudos; comprueba que el ascenso del dataset se reproduce."""
    filas, series = [], {}
    for f in e.itertuples():
        proc = pd.read_csv(PERFILES / f.archivo_perfil)
        crudo = pd.read_csv(PERFILES_RAW / f.archivo_perfil.replace("procesado", "raw"))
        z3 = proc["elevacion_mediana3_m"].to_numpy(float)
        d = proc["distancia_m"].to_numpy(float)
        zr = crudo["elevacion_m"].to_numpy(float)
        a_proc = ascenso_total(z3, f.tipo_recorrido)
        assert abs(a_proc - f.ascenso_total_m) < 0.5, (f.id_ruta, a_proc, f.ascenso_total_m)
        filas.append({
            "id_ruta": f.id_ruta, "ascenso_mediana3_m": a_proc,
            "ascenso_mediana5_m": ascenso_total(mediana_centrada(zr, 5), f.tipo_recorrido),
            "ascenso_crudo_m": ascenso_total(zr, f.tipo_recorrido),
            "tobler_h": tobler_horas(d, z3, f.tipo_recorrido),
            "paso_muestreo_mediano_m": float(np.median(np.diff(d))),
        })
        series[f.id_ruta] = (d, z3, f.tipo_recorrido)
    p = pd.DataFrame(filas)
    p["razon_crudo_sobre_mediana3"] = p["ascenso_crudo_m"] / p["ascenso_mediana3_m"]
    return p, series


# ------------------------------------------------------------------ bloques
def tabla_indicador(e, p):
    t = e[["id_ruta", "id_destino", "tipo_recorrido", "distancia_total_km", "ascenso_total_m", "elevacion_max_m"]].copy()
    t["componente_distancia_h"] = t["distancia_total_km"] / V_KMH
    t["componente_ascenso_h"] = t["ascenso_total_m"] / R_M_H
    t["hen_horas_equivalentes"] = horas_equivalentes(t["distancia_total_km"], t["ascenso_total_m"])
    t["posicion_esfuerzo"] = rangos(t["hen_horas_equivalentes"]).astype(int)
    t["km_esfuerzo"] = t["distancia_total_km"] + t["ascenso_total_m"] / 100.0
    t["tobler_h_contraste"] = p["tobler_h"].to_numpy()
    t["posicion_tobler"] = rangos(t["tobler_h_contraste"]).astype(int)
    for nombre, col in (("mediana3", "ascenso_mediana3_m"), ("mediana5", "ascenso_mediana5_m"), ("crudo", "ascenso_crudo_m")):
        t[f"hen_con_ascenso_{nombre}_h"] = horas_equivalentes(t["distancia_total_km"], p[col].to_numpy())
    t["altitud_maxima_advertencia_m"] = t["elevacion_max_m"]
    # Se conserva el orden por id_ruta (el mismo de perfiles y e) para alinear todos los cálculos;
    # solo la presentación se ordena por posición.
    return t.drop(columns=["elevacion_max_m"]).reset_index(drop=True)


def bloque_formulaciones(t):
    base = t["hen_horas_equivalentes"].to_numpy()
    return pd.DataFrame([
        {"formulacion": "Naismith (base, 5 km/h; 600 m/h)", "spearman_vs_base": 1.0},
        {"formulacion": "km-esfuerzo (km + m/100)", "spearman_vs_base": spearman(base, t["km_esfuerzo"])},
        {"formulacion": "Tobler sobre el perfil (contraste)", "spearman_vs_base": spearman(base, t["tobler_h_contraste"])},
        {"formulacion": "solo distancia", "spearman_vs_base": spearman(base, t["distancia_total_km"])},
        {"formulacion": "solo ascenso", "spearman_vs_base": spearman(base, t["ascenso_total_m"])},
        {"formulacion": "altitud máxima (variable ajena al indicador)", "spearman_vs_base": spearman(base, t["altitud_maxima_advertencia_m"])},
    ])


def bloque_parametros(t):
    filas, ranks = [], {}
    base = t["hen_horas_equivalentes"].to_numpy()
    for v in REJILLA_V:
        for r in REJILLA_R:
            h = horas_equivalentes(t["distancia_total_km"], t["ascenso_total_m"], v, r)
            rk = rangos(h)
            ranks[(v, r)] = rk
            filas.append({"v_kmh": v, "r_m_h": r, "spearman_vs_base": spearman(base, h),
                          "max_desplazamiento_posiciones": float(np.abs(rk - rangos(base)).max()),
                          "top5_igual_a_base": set(t.id_ruta[rk <= 5]) == set(t.id_ruta[t.posicion_esfuerzo <= 5])})
    return pd.DataFrame(filas), ranks


def bloque_dem(t, p):
    base = rangos(t["hen_horas_equivalentes"])
    d = t["distancia_total_km"].to_numpy()
    filas, ranks = [], {}
    for nombre, col in (("mediana3 (base)", "ascenso_mediana3_m"), ("mediana5", "ascenso_mediana5_m"), ("crudo sin filtrar", "ascenso_crudo_m")):
        h = horas_equivalentes(d, p[col].to_numpy())
        rk = rangos(h); ranks[nombre] = rk
        filas.append({"ascenso_usado": nombre, "spearman_vs_base": spearman(t["hen_horas_equivalentes"], h),
                      "max_desplazamiento_posiciones": float(np.abs(rk - base).max()),
                      "mediana_razon_ascenso_vs_base": float(np.median(p[col] / p["ascenso_mediana3_m"]))})
    return pd.DataFrame(filas), ranks


def bloque_monte_carlo(e, series, t):
    """Ruido aleatorio gaussiano adicional sobre la elevación, con el mismo filtro de mediana 3."""
    rng = np.random.default_rng(SEMILLA)
    filas, intervalos = [], {}
    base_rk = rangos(t.set_index("id_ruta").loc[e.id_ruta, "hen_horas_equivalentes"])
    for sigma in SIGMAS_DEM_M:
        rk_sim, asc_sim = [], []
        for _ in range(N_SIMULACIONES):
            a = []
            for f in e.itertuples():
                d, z3, tipo = series[f.id_ruta]
                z = mediana_centrada(z3 + rng.normal(0.0, sigma, len(z3)), 3)
                a.append(ascenso_total(z, tipo))
            a = np.array(a)
            asc_sim.append(a)
            rk_sim.append(rangos(horas_equivalentes(e.distancia_total_km, a)))
        rk_sim, asc_sim = np.array(rk_sim), np.array(asc_sim)
        intervalos[sigma] = np.percentile(rk_sim, [5, 95], axis=0)
        for i, ruta in enumerate(e.id_ruta):
            filas.append({"sigma_dem_m": sigma, "id_ruta": ruta, "posicion_base": int(base_rk[i]),
                          "posicion_p05": float(intervalos[sigma][0, i]), "posicion_p95": float(intervalos[sigma][1, i]),
                          "ascenso_mediano_m": float(np.median(asc_sim[:, i])),
                          "ascenso_p05_m": float(np.percentile(asc_sim[:, i], 5)),
                          "ascenso_p95_m": float(np.percentile(asc_sim[:, i], 95))})
    return pd.DataFrame(filas)


def bloque_intervalos(t, ranks_param, ranks_dem, mc):
    base = t.set_index("id_ruta")["posicion_esfuerzo"]
    filas = []
    for i, ruta in enumerate(t["id_ruta"]):  # mismo orden (por id_ruta) que ranks_*
        p = [rk[i] for rk in ranks_param.values()]
        d = [rk[i] for rk in ranks_dem.values()]
        m = mc[mc.id_ruta == ruta]
        filas.append({
            "id_ruta": ruta, "posicion_base": int(base[ruta]),
            "rango_parametros_min": min(p), "rango_parametros_max": max(p),
            "rango_dem_min": min(d), "rango_dem_max": max(d),
            "rango_montecarlo_p05_min": float(m.posicion_p05.min()), "rango_montecarlo_p95_max": float(m.posicion_p95.max()),
        })
    r = pd.DataFrame(filas)
    r["posicion_min_global"] = r[["rango_parametros_min", "rango_dem_min", "rango_montecarlo_p05_min"]].min(axis=1)
    r["posicion_max_global"] = r[["rango_parametros_max", "rango_dem_max", "rango_montecarlo_p95_max"]].max(axis=1)
    r["amplitud_posiciones"] = r["posicion_max_global"] - r["posicion_min_global"]
    return r.sort_values("posicion_base").reset_index(drop=True)


def bloque_contraste_kmeans(t, e):
    """Compara el ordenamiento continuo con K-means k=2 (4 variables base) sin convertirlo en clase."""
    spec = importlib.util.spec_from_file_location("validar", RAIZ / "06_scripts/validar_metodologia_clasificacion.py")
    val = importlib.util.module_from_spec(spec); spec.loader.exec_module(val)
    x, mejor, _, lab = val.particion(e, val.VARIABLES, 2)
    c0, c1 = x[lab == 0].mean(axis=0), x[lab == 1].mean(axis=0)
    eje = (c1 - c0) / np.linalg.norm(c1 - c0)
    puntaje = (x - (c0 + c1) / 2) @ eje
    h = horas_equivalentes(e.distancia_total_km, e.ascenso_total_m)
    # mejor umbral de HEN contra la partición k=2 (ARI)
    cortes = np.sort(np.unique(h))
    mejor_ari, mejor_corte = -1.0, np.nan
    for c in cortes:
        a = adjusted_rand_score(lab, (h >= c).astype(int))
        if a > mejor_ari:
            mejor_ari, mejor_corte = a, c
    g1 = h[lab == 1]
    arriba = list(e.id_ruta[(lab == 0) & (h >= g1.min())])
    auc = float(np.mean([(a > b) + 0.5 * (a == b) for a in g1 for b in h[lab == 0]]))
    xh = StandardScaler().fit_transform(h.reshape(-1, 1))
    lab_h = KMeans(2, random_state=0, n_init=10).fit(xh).labels_
    ordenado = np.sort(h)[::-1]
    brechas = pd.DataFrame({"entre_posiciones": [f"{i + 1}-{i + 2}" for i in range(len(h) - 1)],
                            "brecha_h": ordenado[:-1] - ordenado[1:]}).sort_values("brecha_h", ascending=False)
    res = {
        "spearman_hen_vs_puntaje_kmeans_k2": spearman(h, puntaje),
        "auc_hen_grupo_mayor_ascenso_vs_resto": auc,
        "mejor_umbral_hen_h": float(mejor_corte), "ari_mejor_umbral_vs_kmeans_k2": float(mejor_ari),
        "rutas_del_grupo_menor_con_hen_igual_o_mayor_que_la_minima_del_grupo_mayor": arriba,
        "ari_kmeans_1d_sobre_hen_vs_kmeans_k2": float(adjusted_rand_score(lab, lab_h)),
        "grupo_mayor_kmeans_k2": sorted(e.id_ruta[lab == 1]),
        "mayor_brecha_consecutiva_h": float(brechas.iloc[0].brecha_h), "mayor_brecha_entre": brechas.iloc[0].entre_posiciones,
        "rango_hen_h": [float(h.min()), float(h.max())],
    }
    puntos = pd.DataFrame({"id_ruta": e.id_ruta, "grupo_kmeans_k2_orden_por_ascenso": lab,
                           "puntaje_kmeans_eje_centroides": puntaje, "hen_horas_equivalentes": h})
    return res, puntos, brechas


# ------------------------------------------------------------------ figuras
def figuras(t, inter, puntos, fecha):
    FIGURAS.mkdir(parents=True, exist_ok=True)
    t = t.sort_values("posicion_esfuerzo")
    g = puntos.set_index("id_ruta")["grupo_kmeans_k2_orden_por_ascenso"]
    tt = t.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(1, 2, figsize=(14, 7), gridspec_kw={"width_ratios": [3, 2]})
    y = np.arange(len(tt))
    ax[0].barh(y, tt.componente_distancia_h, color="#8aa9c2", label="distancia ÷ 5 km/h")
    ax[0].barh(y, tt.componente_ascenso_h, left=tt.componente_distancia_h, color="#e08a5b", label="ascenso ÷ 600 m/h")
    ax[0].set_yticks(y)
    ax[0].set_yticklabels([f"{r}{'*' if g[r] == 1 else ''}" for r in tt.id_ruta])
    for i, h in enumerate(tt.hen_horas_equivalentes):
        ax[0].text(h + 0.03, i, f"{h:.2f}", va="center", fontsize=8)
    ax[0].set_xlabel("horas-equivalentes de referencia (HEN) — estimadas, no medidas")
    ax[0].set_title("Indicador de esfuerzo de referencia (* = grupo mayor ascenso de K-means k=2)")
    ax[0].legend(loc="lower right"); ax[0].grid(axis="x", alpha=.25)
    ii = inter.set_index("id_ruta").loc[tt.id_ruta].reset_index()
    ax[1].hlines(y, ii.posicion_min_global, ii.posicion_max_global, color="#555")
    ax[1].plot(ii.posicion_base, y, "o", color="#d1603d")
    ax[1].set_yticks(y); ax[1].set_yticklabels([f"{r} · alt. {a:,.0f} m".replace(",", " ") for r, a in zip(tt.id_ruta, tt.altitud_maxima_advertencia_m)], fontsize=8)
    ax[1].set_xlabel("posición (1 = mayor esfuerzo): base y rango en sensibilidades")
    ax[1].set_title("Incertidumbre del orden · la altitud es advertencia aparte")
    ax[1].invert_xaxis(); ax[1].grid(axis="x", alpha=.25)
    fig.tight_layout(); fig.savefig(FIGURAS / f"indicador_esfuerzo_{fecha}.png", dpi=140); plt.close(fig)


def main():
    ap = ArgumentParser(description=__doc__)
    ap.add_argument("--fecha", required=True)
    fecha = date.fromisoformat(ap.parse_args().fecha).isoformat()
    e = cargar()
    p, series = perfiles(e)
    t = tabla_indicador(e, p)
    form = bloque_formulaciones(t)
    param, rk_param = bloque_parametros(t)
    dem, rk_dem = bloque_dem(t, p)
    mc = bloque_monte_carlo(e, series, t)
    inter = bloque_intervalos(t, rk_param, rk_dem, mc)
    res_k, puntos, brechas = bloque_contraste_kmeans(t, e)
    figuras(t, inter, puntos, fecha)
    salidas = {"indicador_esfuerzo": t, "indicador_formulaciones": form, "indicador_sensibilidad_parametros": param,
               "indicador_sensibilidad_dem": dem, "indicador_dem_perfiles": p, "indicador_dem_montecarlo": mc,
               "indicador_intervalos_posicion": inter, "indicador_contraste_kmeans": puntos, "indicador_brechas": brechas}
    salidas["indicador_esfuerzo"] = t.sort_values("posicion_esfuerzo").reset_index(drop=True)
    for nombre, tabla in salidas.items():
        tabla.to_csv(TABLAS / f"{nombre}_{fecha}.csv", index=False, encoding="utf-8")
    resumen = {
        "fecha": fecha, "n_rutas": int(len(e)),
        "definicion": "HEN = distancia_total_km / V + ascenso_total_m / R (regla de Naismith)",
        "parametros": {"V_kmh": V_KMH, "R_m_h": R_M_H, "rejilla_v": list(REJILLA_V), "rejilla_r": list(REJILLA_R),
                       "sigmas_dem_m": list(SIGMAS_DEM_M), "n_simulaciones": N_SIMULACIONES, "semilla": SEMILLA},
        "naturaleza": "horas-equivalentes estimadas de referencia; no son tiempos medidos ni clases",
        "altitud": "advertencia separada; no entra en el indicador",
        "formulaciones": form.set_index("formulacion")["spearman_vs_base"].round(4).to_dict(),
        "sensibilidad_parametros": {"spearman_min": float(param.spearman_vs_base.min()),
                                    "max_desplazamiento_posiciones": float(param.max_desplazamiento_posiciones.max()),
                                    "top5_estable_en": f"{int(param.top5_igual_a_base.sum())}/{len(param)}"},
        "sensibilidad_dem": dem.set_index("ascenso_usado")[["spearman_vs_base", "max_desplazamiento_posiciones", "mediana_razon_ascenso_vs_base"]].round(4).to_dict("index"),
        "razon_ascenso_crudo_sobre_mediana3": {"min": float(p.razon_crudo_sobre_mediana3.min()), "max": float(p.razon_crudo_sobre_mediana3.max())},
        "amplitud_posiciones": {"mediana": float(inter.amplitud_posiciones.median()), "maxima": float(inter.amplitud_posiciones.max())},
        "contraste_kmeans_k2": res_k,
        "versiones": {"pandas": pd.__version__, "numpy": np.__version__, "sklearn": __import__("sklearn").__version__},
        "habilitacion": "NO: no crea clases, no habilita recomendaciones ni escribe validacion_modelo_final.json",
    }
    (TABLAS / f"indicador_resumen_{fecha}.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(salidas["indicador_esfuerzo"].round(2).to_string(index=False)); print(form.round(3).to_string(index=False))
    print(param.describe().round(3).to_string()); print(dem.round(3).to_string(index=False))
    print(p[["id_ruta", "ascenso_mediana3_m", "ascenso_mediana5_m", "ascenso_crudo_m", "razon_crudo_sobre_mediana3"]].round(2).to_string(index=False))
    print(inter.round(1).to_string(index=False)); print(json.dumps(res_k, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
