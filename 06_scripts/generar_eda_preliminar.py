"""Genera un EDA preliminar de las rutas actualmente elegibles.

El resultado es diagnóstico y no ajusta K-means. Se debe volver a ejecutar
cuando el inventario alcance la muestra mínima definida en la metodología.
"""

import argparse
import os
from pathlib import Path
import sys

# Debe fijarse antes de importar NumPy/Matplotlib: evita el fallo local de MKL
# al consultar hilos en Windows (0xC06D007F).
if sys.platform == "win32":
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
DATASET = RAIZ / "07_resultados" / "tablas" / "dataset_clasificacion_rutas.csv"
GRAFICOS = RAIZ / "07_resultados" / "graficos"
EVIDENCIAS = RAIZ / "08_evidencias"
DOCUMENTACION = RAIZ / "01_documentacion"

VARIABLES = {
    "distancia_total_km": "Distancia total (km)",
    "ascenso_total_m": "Ascenso total (m)",
    "elevacion_max_m": "Elevación máxima (m)",
    "pendiente_media_abs_pct": "Pendiente media abs. (%)",
    "pendiente_p95_abs_pct": "Pendiente p95 abs. (%)",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", required=True, help="Fecha de la instantánea (AAAA-MM-DD)")
    parser.add_argument("--evidencia", required=True, help="Código de evidencia, por ejemplo E25")
    parser.add_argument("--rutas-esperadas", required=True, type=int)
    args = parser.parse_args()
    if not args.evidencia.startswith("E") or not args.evidencia[1:].isdigit():
        parser.error("--evidencia debe tener el formato E25")

    datos = pd.read_csv(DATASET)
    elegibles = datos.loc[datos["estado_modelado"].eq("elegible_actual")].copy()
    assert len(elegibles) >= 3
    assert len(elegibles) == args.rutas_esperadas, (
        f"Se esperaban {args.rutas_esperadas} rutas elegibles y se encontraron {len(elegibles)}. "
        "Use un nuevo código de evidencia para una muestra nueva."
    )
    assert not elegibles[list(VARIABLES)].isna().any().any()

    GRAFICOS.mkdir(parents=True, exist_ok=True)
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({"font.family": "Arial", "font.size": 9})
    figura, ejes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    for eje, (variable, etiqueta) in zip(ejes.flat[:5], VARIABLES.items()):
        valores = elegibles[variable]
        numero_barras = min(6, max(3, int(np.sqrt(len(valores))) + 1))
        eje.hist(valores, bins=numero_barras, color="#1769aa", alpha=0.85, edgecolor="white")
        eje.axvline(valores.median(), color="#c4472d", linewidth=1.8, linestyle="--", label="Mediana")
        eje.set_title(etiqueta, fontweight="bold")
        eje.set_ylabel("Número de rutas")
        eje.grid(axis="y", alpha=0.25)
        eje.legend(frameon=False)

    correlacion = elegibles[list(VARIABLES)].corr(method="spearman")
    eje = ejes.flat[5]
    imagen = eje.imshow(correlacion, vmin=-1, vmax=1, cmap="RdBu_r")
    abreviaturas = ["Dist.", "Ascenso", "Elev. máx.", "Pend. media", "Pend. p95"]
    eje.set_xticks(range(len(abreviaturas)), abreviaturas, rotation=40, ha="right")
    eje.set_yticks(range(len(abreviaturas)), abreviaturas)
    eje.set_title("Correlación de Spearman", fontweight="bold")
    for fila in range(len(abreviaturas)):
        for columna in range(len(abreviaturas)):
            valor = correlacion.iloc[fila, columna]
            eje.text(columna, fila, f"{valor:.2f}", ha="center", va="center", color="white" if abs(valor) > 0.55 else "black")
    figura.colorbar(imagen, ax=eje, fraction=0.046, pad=0.04)
    figura.suptitle(
        f"Análisis exploratorio preliminar · {len(elegibles)} rutas elegibles",
        fontsize=16,
        fontweight="bold",
    )
    figura.text(
        0.5,
        0.005,
        "Diagnóstico previo al modelo. La muestra se ampliará antes del ajuste final de K-means.",
        ha="center",
        fontsize=10,
    )

    salida_svg = GRAFICOS / f"eda_preliminar_variables_{len(elegibles)}_rutas_{args.fecha}.svg"
    salida_png = EVIDENCIAS / f"{args.evidencia}_eda_preliminar_{len(elegibles)}_rutas_{args.fecha}.png"
    salida_md = DOCUMENTACION / f"eda_preliminar_{len(elegibles)}_rutas_{args.fecha}.md"
    for salida in (salida_svg, salida_png, salida_md):
        if salida.exists():
            raise FileExistsError(f"La instantánea ya existe: {salida.name}. Use un código y fecha nuevos.")
    figura.savefig(salida_svg, dpi=150, bbox_inches="tight")
    figura.savefig(salida_png, dpi=170, bbox_inches="tight")
    plt.close(figura)
    # Matplotlib deja espacios finales en muchas líneas del SVG. Se eliminan
    # para mantener el artefacto estable y compatible con `git diff --check`.
    texto_svg = salida_svg.read_text(encoding="utf-8")
    salida_svg.write_text(
        "\n".join(linea.rstrip() for linea in texto_svg.splitlines()) + "\n",
        encoding="utf-8",
    )

    resumen = elegibles[list(VARIABLES)].describe().loc[["min", "50%", "max"]]
    correlaciones = []
    for i, variable_a in enumerate(VARIABLES):
        for variable_b in list(VARIABLES)[i + 1 :]:
            correlaciones.append((abs(correlacion.loc[variable_a, variable_b]), variable_a, variable_b, correlacion.loc[variable_a, variable_b]))
    correlaciones.sort(reverse=True)
    concentracion_destinos = elegibles.groupby("id_destino").size().sort_values(ascending=False)
    rutas_dos_destinos = int(concentracion_destinos.head(2).sum())
    alertas_atipicos = []
    for variable, etiqueta in VARIABLES.items():
        q1, q3 = elegibles[variable].quantile([0.25, 0.75])
        iqr = q3 - q1
        fuera = elegibles.loc[
            (elegibles[variable] < q1 - 1.5 * iqr)
            | (elegibles[variable] > q3 + 1.5 * iqr),
            ["id_ruta", variable],
        ]
        for ruta, valor in fuera.itertuples(index=False, name=None):
            alertas_atipicos.append((ruta, etiqueta, valor))

    lineas = [
        f"# Análisis exploratorio preliminar ({args.fecha})",
        "",
        "## Alcance",
        "",
        f"Se analizaron **{len(elegibles)} rutas elegibles** de {len(datos)} rutas procesadas. Este documento no presenta una clasificación final ni entrena K-means. Su objetivo es anticipar problemas de escala, redundancia y valores extremos antes de cerrar el inventario.",
        "",
        "## Resumen de variables",
        "",
        "| Variable | Mínimo | Mediana | Máximo |",
        "|---|---:|---:|---:|",
    ]
    for variable, etiqueta in VARIABLES.items():
        lineas.append(
            f"| {etiqueta} | {resumen.loc['min', variable]:.2f} | {resumen.loc['50%', variable]:.2f} | {resumen.loc['max', variable]:.2f} |"
        )
    lineas.extend(
        [
            "",
            "## Hallazgos provisionales",
            "",
            f"- La mayor correlación absoluta observada es **{correlaciones[0][3]:.2f}** entre `{correlaciones[0][1]}` y `{correlaciones[0][2]}`. Debe revisarse nuevamente con el inventario completo para decidir si ambas variables permanecen en el modelo.",
            "- Las escalas son muy distintas: kilómetros, metros y porcentajes. Se confirma la necesidad de aplicar `StandardScaler` antes de K-means.",
            "- Las rutas cortas de reservas y los ascensos de mayor desnivel amplían el rango físico. Esa diversidad es útil, pero exige revisar la estabilidad de los grupos y no interpretar el número de clúster como una dificultad oficial.",
            f"- {rutas_dos_destinos} de las {len(elegibles)} rutas provienen de los dos lugares amplios (`id_destino`) con más rutas; un mismo lugar puede contener llegadas distintas. Esa concentración puede influir en los grupos; se revisará la diversidad geográfica antes del ajuste final.",
            "- No se eliminó ninguna observación en esta etapa. La regla de Tukey (1,5 × rango intercuartílico) solo señala valores para revisión.",
            "",
            "## Detección descriptiva de valores atípicos",
            "",
            "| Ruta | Variable | Valor |",
            "|---|---|---:|",
            *([f"| {ruta} | {etiqueta} | {valor:.2f} |" for ruta, etiqueta, valor in alertas_atipicos]
              or ["| — | Ninguna alerta con la regla aplicada | — |"]),
            "",
            "Antes de cualquier exclusión se revisarán la fuente del trazado, el perfil y la plausibilidad física. Con esta muestra pequeña, los cuartiles son inestables.",
            "",
            "## Próximo uso",
            "",
            "Al cerrar el inventario se volverá a ejecutar este análisis con al menos 20 rutas elegibles. Después se compararán soluciones K-means para varios valores de `k`, estabilidad por semillas y validación jerárquica de Ward.",
            "",
            f"Figura reproducible: `07_resultados/graficos/{salida_svg.name}`.",
            f"Evidencia: `08_evidencias/{salida_png.name}`.",
            "",
        ]
    )
    salida_md.write_text("\n".join(lineas), encoding="utf-8")

    print(f"Rutas elegibles analizadas: {len(elegibles)}")
    print(f"Figura: {salida_svg.name}")
    print(f"Evidencia: {salida_png.name}")
    print(f"Informe: {salida_md.name}")


if __name__ == "__main__":
    main()
