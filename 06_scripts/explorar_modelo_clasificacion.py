"""Evalúa agrupamientos exploratorios sin publicar un modelo final.

Uso: python 06_scripts/explorar_modelo_clasificacion.py --fecha 2026-10-13
Los CSV de salida son resultados derivados; el inventario y dataset no se editan.
"""

from argparse import ArgumentParser
from datetime import date
import os
from pathlib import Path
import sys

# En este entorno Windows MKL falla al consultar sus hilos con su capa por
# defecto. La capa secuencial permite ejecutar KMeans sin modificar el entorno.
if sys.platform == "win32":
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"

import numpy as np
import pandas as pd
from scipy.cluster.vq import ClusterError, kmeans2, vq
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler


RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "07_resultados/tablas/dataset_clasificacion_rutas.csv"
SALIDA = RAIZ / "07_resultados/tablas"
DOCUMENTACION = RAIZ / "01_documentacion"
META_FINAL = 20
VARIABLES_BASE = [
    "distancia_total_km",
    "ascenso_total_m",
    "elevacion_max_m",
    "pendiente_media_abs_pct",
]
VARIABLES_REDUNDANTES = VARIABLES_BASE + ["pendiente_p95_abs_pct"]
RUTAS_POR_CONFIRMAR = {"R011", "R013"}
VARIANTE_ACCESO_COMPARTIDO = "R020"
NUEVA_VARIANTE_COMPARTIDA = "R021"
RUTA_ATIPICA_EDA = "R006"
RUTA_NUEVA_ILALO = "R022"
RUTA_NUEVA_GUAGRAPAMBA = "R023"
RUTA_GUARUMOS = "R026"
RUTA_CORTA_MORASPUNGO = "R027"


def cargar_elegibles() -> pd.DataFrame:
    datos = pd.read_csv(ENTRADA)
    assert datos["id_ruta"].is_unique, "Hay ID de ruta duplicados"
    elegibles = datos.loc[datos["estado_modelado"].eq("elegible_actual")].copy()
    assert len(elegibles) >= 3, "No hay muestra para un experimento de 2 grupos"
    assert elegibles["id_destino"].notna().all()
    for variable in VARIABLES_REDUNDANTES:
        columna = pd.to_numeric(elegibles[variable], errors="coerce")
        assert np.isfinite(columna.to_numpy()).all(), f"Valores no finitos en {variable}"
        assert columna.nunique() > 1, f"Variable constante: {variable}"
        elegibles[variable] = columna
    return elegibles.sort_values("id_ruta").reset_index(drop=True)


def silueta_euclidea(datos: np.ndarray, etiquetas: np.ndarray) -> float:
    """Silueta para una muestra pequeña; evita el fallo local de BLAS/threadpoolctl."""
    distancias = squareform(pdist(datos, metric="euclidean"))
    valores = []
    for indice, grupo in enumerate(etiquetas):
        pares_mismo = np.flatnonzero(etiquetas == grupo)
        pares_mismo = pares_mismo[pares_mismo != indice]
        if not len(pares_mismo):
            raise ValueError("La silueta no se interpreta con grupos unitarios")
        a = float(np.mean(distancias[indice, pares_mismo]))
        b = min(
            float(np.mean(distancias[indice, etiquetas == otro]))
            for otro in np.unique(etiquetas)
            if otro != grupo
        )
        valores.append((b - a) / max(a, b) if max(a, b) else 0.0)
    return float(np.mean(valores))


def evaluar(escenario: str, datos: pd.DataFrame, variables: list[str], motor: str = "scipy"):
    if motor not in {"scipy", "sklearn"}:
        raise ValueError(f"Motor de K-means no reconocido: {motor}")
    escalados = StandardScaler().fit_transform(datos[variables])
    resultados = []
    asignaciones = []
    for k in range(2, min(4, len(datos) - 1) + 1):
        intentos = []
        for semilla in range(30):
            if motor == "sklearn":
                ajuste = KMeans(n_clusters=k, random_state=semilla, n_init=10).fit(escalados)
                grupos_intento = ajuste.labels_
                inercia_intento = float(ajuste.inertia_)
            else:
                try:
                    centros, _ = kmeans2(
                        escalados, k, iter=100, minit="++", missing="raise", rng=semilla
                    )
                except ClusterError:
                    continue
                grupos_intento, distancias = vq(escalados, centros)
                inercia_intento = float(np.sum(distancias ** 2))
            if len(np.unique(grupos_intento)) != k:
                continue
            if np.min(np.bincount(grupos_intento, minlength=k)) < 2:
                continue
            intentos.append((inercia_intento, grupos_intento))
        if not intentos:
            continue
        inercia, grupos = min(intentos, key=lambda intento: intento[0])
        tamanos = np.bincount(grupos, minlength=k)
        ward = AgglomerativeClustering(n_clusters=k, linkage="ward")
        grupos_ward = ward.fit_predict(escalados)
        estabilidad = [adjusted_rand_score(grupos, variante) for _, variante in intentos]
        resultados.append(
            {
                "escenario": escenario,
                "n_rutas": len(datos),
                "variables": "|".join(variables),
                "k": k,
                "silueta": round(
                    silhouette_score(escalados, grupos)
                    if motor == "sklearn" else silueta_euclidea(escalados, grupos), 4
                ),
                "inercia": round(inercia, 4),
                "tamano_minimo": int(np.min(tamanos)),
                "tamano_maximo": int(np.max(tamanos)),
                "ari_ward": round(float(adjusted_rand_score(grupos, grupos_ward)), 4),
                "ari_semillas_min": round(float(min(estabilidad)), 4),
                "semillas_validas": len(intentos),
            }
        )
        for fila, grupo in zip(datos.itertuples(index=False), grupos):
            asignaciones.append(
                {
                    "escenario": escenario,
                    "k": k,
                    "id_ruta": fila.id_ruta,
                    "id_destino": fila.id_destino,
                    "grupo_numerico_sin_orden": int(grupo),
                }
            )
    return resultados, asignaciones


def construir_escenarios(elegibles: pd.DataFrame, motor: str):
    """Prueba sensibilidad a fuentes dudosas, atípicos y destinos dominantes."""
    escenarios = [
        ("base_4_variables", elegibles, VARIABLES_BASE),
        (
            "sin_variable_distancia",
            elegibles,
            [variable for variable in VARIABLES_BASE if variable != "distancia_total_km"],
        ),
        (
            "sin_variable_ascenso",
            elegibles,
            [variable for variable in VARIABLES_BASE if variable != "ascenso_total_m"],
        ),
        (
            "sin_yanacocha_pendiente",
            elegibles.loc[~elegibles["id_ruta"].isin(RUTAS_POR_CONFIRMAR)].copy(),
            VARIABLES_BASE,
        ),
        (
            "sin_r020_acceso_compartido",
            elegibles.loc[~elegibles["id_ruta"].eq(VARIANTE_ACCESO_COMPARTIDO)].copy(),
            VARIABLES_BASE,
        ),
        (
            "sin_r021_senderos_1_2",
            elegibles.loc[~elegibles["id_ruta"].eq(NUEVA_VARIANTE_COMPARTIDA)].copy(),
            VARIABLES_BASE,
        ),
        (
            "sin_r006_atipico_eda",
            elegibles.loc[~elegibles["id_ruta"].eq(RUTA_ATIPICA_EDA)].copy(),
            VARIABLES_BASE,
        ),
        (
            "sin_r022_ilalo_pendiente",
            elegibles.loc[~elegibles["id_ruta"].eq(RUTA_NUEVA_ILALO)].copy(),
            VARIABLES_BASE,
        ),
    ]
    if RUTA_NUEVA_GUAGRAPAMBA in set(elegibles["id_ruta"]):
        escenarios.append((
            "sin_r023_guagrapamba_pendiente",
            elegibles.loc[~elegibles["id_ruta"].eq(RUTA_NUEVA_GUAGRAPAMBA)].copy(),
            VARIABLES_BASE,
        ))
    if RUTA_GUARUMOS in set(elegibles["id_ruta"]):
        escenarios.append((
            "sin_r026_guarumos_solapamiento_dem",
            elegibles.loc[~elegibles["id_ruta"].eq(RUTA_GUARUMOS)].copy(),
            VARIABLES_BASE,
        ))
    if RUTA_CORTA_MORASPUNGO in set(elegibles["id_ruta"]):
        escenarios.append((
            "sin_r027_sendero_corto",
            elegibles.loc[~elegibles["id_ruta"].eq(RUTA_CORTA_MORASPUNGO)].copy(),
            VARIABLES_BASE,
        ))
    for destino, cantidad in elegibles.groupby("id_destino").size().items():
        if cantidad >= 2:
            escenarios.append(
                (
                    f"sin_destino_{destino.lower()}",
                    elegibles.loc[~elegibles["id_destino"].eq(destino)].copy(),
                    VARIABLES_BASE,
                )
            )
    if motor == "sklearn":
        escenarios.append(("base_5_variables", elegibles, VARIABLES_REDUNDANTES))
    return escenarios


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", required=True, help="Fecha real de ejecución, AAAA-MM-DD")
    parser.add_argument("--motor", choices=["scipy", "sklearn"], default="scipy")
    parser.add_argument("--identificador", default="", help="Sufijo opcional para preservar cortes anteriores de la misma fecha")
    argumentos = parser.parse_args()
    fecha = date.fromisoformat(argumentos.fecha).isoformat()
    motor = argumentos.motor
    identificador = argumentos.identificador.strip()
    assert not identificador or (identificador.isascii() and identificador.replace("_", "").isalnum()), "Identificador inválido"

    elegibles = cargar_elegibles()
    # El ensayo puede repetirse al alcanzar la meta para estudiar sensibilidad;
    # esta rutina no publica clases ni constituye la validación final.
    escenarios = construir_escenarios(elegibles, motor)
    resultados = []
    asignaciones = []
    escenarios_sin_solucion = []
    for nombre, datos, variables in escenarios:
        medidas, etiquetas = evaluar(nombre, datos, variables, motor=motor)
        if not medidas:
            escenarios_sin_solucion.append(nombre)
        resultados.extend(medidas)
        asignaciones.extend(etiquetas)

    assert resultados, "Ningún agrupamiento cumple el mínimo de 2 rutas por grupo"
    tabla = pd.DataFrame(resultados).sort_values(["escenario", "k"])
    grupos = pd.DataFrame(asignaciones).sort_values(["escenario", "k", "id_ruta"])
    comparaciones = []
    for escenario_sensibilidad, _, _ in escenarios:
        if not escenario_sensibilidad.startswith("sin_"):
            continue
        for k in sorted(grupos["k"].unique()):
            izquierda = grupos.loc[grupos["escenario"].eq("base_4_variables") & grupos["k"].eq(k)]
            derecha = grupos.loc[
                grupos["escenario"].eq(escenario_sensibilidad) & grupos["k"].eq(k)
            ]
            pares = izquierda.merge(derecha, on="id_ruta", suffixes=("_base", "_sensibilidad"))
            if len(pares) >= 2:
                comparaciones.append(
                    (
                        escenario_sensibilidad,
                        k,
                        len(pares),
                        adjusted_rand_score(
                            pares["grupo_numerico_sin_orden_base"],
                            pares["grupo_numerico_sin_orden_sensibilidad"],
                        ),
                    )
                )
    sufijo = "" if motor == "scipy" else "_sklearn"
    fecha_archivo = fecha + ("_" + identificador if identificador else "")
    tabla.to_csv(SALIDA / f"evaluacion_clustering_exploratorio{sufijo}_{fecha_archivo}.csv", index=False)
    grupos.to_csv(SALIDA / f"grupos_exploratorios{sufijo}_{fecha_archivo}.csv", index=False)

    corr = elegibles[VARIABLES_REDUNDANTES].corr()
    nota = [
        "# Ensayo exploratorio de clasificación",
        "",
        f"**Fecha:** {fecha}. **Rutas elegibles provisionales:** {len(elegibles)} de {META_FINAL} requeridas para el entrenamiento final.",
        "",
        "No es un modelo final ni una calificación oficial de dificultad. Los números de grupo no tienen orden de exigencia.",
        "",
        "## Diseño",
        "",
        "- Unidad: alternativa de ruta con `estado_modelado=elegible_actual`; las demás rutas no entran al ajuste.",
        "- Variables base: distancia total (km), ascenso total (m), elevación máxima (m), pendiente media absoluta (%).",
        (
            "- Cada escenario ajusta su propio `StandardScaler`. Se ejecuta K-means de scikit-learn con `n_init=10`, 30 semillas y se conserva la menor inercia válida. En Windows, el proceso fija `MKL_THREADING_LAYER=SEQUENTIAL` antes de importar NumPy para evitar el fallo local de MKL. Se usa `silhouette_score` de scikit-learn."
            if motor == "sklearn" else
            "- Cada escenario ajusta su propio `StandardScaler`. El ensayo ejecuta K-means de SciPy con 30 semillas reproducibles y conserva la menor inercia válida. La silueta se calcula con distancias euclidianas de SciPy."
        ),
        "- Se prueban 2 a 4 grupos, descartando soluciones con grupos unitarios; Ward y la variación entre semillas sirven como controles, no como etiquetas verdaderas.",
        f"- Correlación entre pendiente media y p95: **{corr.loc['pendiente_media_abs_pct', 'pendiente_p95_abs_pct']:.3f}**. La configuración base usa cuatro variables; el escenario alternativo de cinco variables comprueba el efecto de añadir p95 cuando se selecciona scikit-learn.",
        "- Sensibilidad: repetir la configuración base sin R011 y R013, cuyos recorridos completos siguen por confirmar. No modifica su estado en el inventario.",
        "- Sensibilidad adicional: repetir la configuración base sin R020, variante que comparte acceso con R017. No modifica su elegibilidad provisional.",
        "- Sensibilidad adicional: repetir la configuración base sin R021, variante por Senderos 1 y 2 que comparte destino y acceso. Su independencia práctica continúa en revisión.",
        "- Influencia de R006: repetir sin esta ruta, que presenta alertas descriptivas de ascenso y pendiente en el EDA del 17 de octubre. La regla estadística no justifica excluirla del inventario.",
        "- Sensibilidad de R022: repetir sin el sendero Cruz del Ilaló, cuya pendiente elevada y acceso vigente requieren revisión. No equivale a excluirlo del inventario.",
        "- Sensibilidad de R023: repetir sin el sendero a Guagrapamba, cuyo acceso y estado actual requieren revisión. No equivale a excluirlo del inventario.",
        "- Sensibilidad de R026: repetir sin Guarumos por el solapamiento con R005 (excluida) y la pendiente p95 susceptible a artefactos del DSM. No equivale a excluir R026 ni a contar R005.",
        "- Sensibilidad de R027: repetir sin el Sendero del Viento, cuya longitud es corta respecto del conjunto. No modifica su elegibilidad provisional.",
        "- Redundancia de variables: repetir con tres variables retirando, por separado, distancia total o ascenso total. La asociación alta entre ambas motiva el contraste, pero no selecciona todavía un conjunto definitivo.",
        "- Concentración por lugar amplio (`id_destino`): retirar por separado cada grupo con al menos dos rutas elegibles y comparar las asignaciones de las rutas comunes. Estos grupos pueden contener llegadas distintas y no son las alternativas comparables de la interfaz. Un ARI bajo indicaría dependencia de la composición de esta muestra.",
        f"- En este corte, D004=Cerro Pondoña (2 rutas), D009=Reserva Yanacocha (2) y D010=Mindo ({int(elegibles['id_destino'].eq('D010').sum())}). Retirar D009 coincide con el escenario sin R011/R013; no son dos pruebas independientes.",
        "",
        "## Resultados numéricos",
        "",
        "| Escenario | n | k | Silueta | Grupo mínimo | ARI frente a Ward | ARI mínimo entre semillas | Semillas válidas |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for fila in tabla.itertuples(index=False):
        nota.append(
            f"| {fila.escenario} | {fila.n_rutas} | {fila.k} | {fila.silueta:.3f} | "
            f"{fila.tamano_minimo} | {fila.ari_ward:.3f} | {fila.ari_semillas_min:.3f} | {fila.semillas_validas} |"
        )
    if escenarios_sin_solucion:
        nota.extend(["", "## Escenarios sin solución aceptada", ""])
        for nombre in escenarios_sin_solucion:
            nota.append(
                f"- `{nombre}`: ninguna configuración k=2–4 produjo grupos de al menos dos rutas en las 30 semillas probadas. No se calcula silueta ni se sustituye por un valor artificial."
            )
    nota.extend(["", "## Sensibilidad frente a la muestra base", ""])
    for escenario_sensibilidad, k, comunes, ari in comparaciones:
        nota.append(
            f"- `{escenario_sensibilidad}`, k={k}: ARI={ari:.3f} sobre {comunes} rutas presentes en ambos escenarios."
        )
    sin_comparacion = {
        nombre for nombre, _, _ in escenarios if nombre.startswith("sin_")
    } - {nombre for nombre, _, _, _ in comparaciones}
    for nombre in sorted(sin_comparacion):
        nota.append(f"- `{nombre}`: sin partición válida comparable con la base; no se imputa un ARI.")
    nota.extend(
        [
            "",
            "## Lectura y límite",
            "",
            "La silueta, la estabilidad y la concordancia con Ward describen esta muestra pequeña; no miden validez externa ni seguridad de senderos.",
        "Un ARI mínimo alto con pocas semillas válidas no demuestra estabilidad; hay que leerlo junto con `Semillas válidas`.",
            "Los centroides se recalcularán cuando se cierre el inventario. Por ello no se asignan todavía nombres `baja/media/alta` ni se guardan modelos para recomendar al usuario.",
            "Si una configuración cambia notablemente al retirar R011/R013, esa sensibilidad es una razón adicional para posponer la clasificación final.",
            "La lectura de cada escenario debe considerar cuántas semillas produjeron grupos no unitarios; una concordancia perfecta basada en solo dos semillas válidas no acredita robustez.",
            "El escenario de cinco variables solo se calcula con el motor scikit-learn y comprueba la sensibilidad a incluir p95; no decide aún las variables finales." if motor == "sklearn" else "La comparación con cinco variables queda para el ensayo con scikit-learn.",
            "",
            "Archivos derivados: `evaluacion_clustering_exploratorio" + sufijo + "_" + fecha_archivo + ".csv` y `grupos_exploratorios" + sufijo + "_" + fecha_archivo + ".csv`.",
            "",
            "Reproducir desde la raíz: `python 06_scripts/explorar_modelo_clasificacion.py --fecha " + fecha + " --motor " + motor + (" --identificador " + identificador if identificador else "") + "`.",
            "",
        ]
    )
    (DOCUMENTACION / f"ensayo_clustering_exploratorio{sufijo}_{fecha_archivo}.md").write_text(
        "\n".join(nota), encoding="utf-8"
    )
    print(tabla.to_string(index=False))
    print("Ensayo exploratorio completado; no se publicaron clases ni recomendaciones.")


if __name__ == "__main__":
    main()
