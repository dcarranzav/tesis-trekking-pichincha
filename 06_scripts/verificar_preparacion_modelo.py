"""Evalúa si el conjunto elegible está listo para el clustering final.

No ajusta K-means. Genera controles reproducibles que bloquean el entrenamiento
final mientras no se cumpla la muestra mínima definida en la metodología.
"""

from argparse import ArgumentParser
from datetime import date
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
DATASET = RAIZ / "07_resultados" / "tablas" / "dataset_clasificacion_rutas.csv"
SALIDA = RAIZ / "07_resultados" / "tablas" / "diagnostico_preparacion_modelo.csv"
MINIMO_RUTAS = 20
VARIABLES = [
    "distancia_total_km",
    "ascenso_total_m",
    "elevacion_max_m",
    "pendiente_media_abs_pct",
    "pendiente_p95_abs_pct",
]


def main() -> None:
    parser = ArgumentParser(description="Diagnostica la preparación del modelo.")
    parser.add_argument("--fecha", required=True, help="Fecha real de ejecución (AAAA-MM-DD)")
    args = parser.parse_args()
    fecha = date.fromisoformat(args.fecha).isoformat()
    informe = RAIZ / "01_documentacion" / f"diagnostico_preparacion_modelo_{fecha}.md"
    dataset = pd.read_csv(DATASET)
    elegibles = dataset.loc[dataset["estado_modelado"].eq("elegible_actual")].copy()
    matriz = elegibles[VARIABLES]
    correlacion = matriz.corr(method="spearman").abs()
    pares = [
        (correlacion.loc[a, b], a, b)
        for i, a in enumerate(VARIABLES)
        for b in VARIABLES[i + 1 :]
    ]
    maxima_correlacion, variable_a, variable_b = max(pares)

    controles = [
        {
            "control": "muestra_minima",
            "estado": "OK" if len(elegibles) >= MINIMO_RUTAS else "BLOQUEADO",
            "valor": len(elegibles),
            "umbral": f">={MINIMO_RUTAS}",
            "detalle": "Número de alternativas elegibles para el ajuste final",
        },
        {
            "control": "valores_faltantes",
            "estado": "OK" if int(matriz.isna().sum().sum()) == 0 else "ERROR",
            "valor": int(matriz.isna().sum().sum()),
            "umbral": "0",
            "detalle": "Celdas faltantes en las cinco variables candidatas",
        },
        {
            "control": "filas_duplicadas",
            "estado": "OK" if int(matriz.duplicated().sum()) == 0 else "ADVERTENCIA",
            "valor": int(matriz.duplicated().sum()),
            "umbral": "0",
            "detalle": "Perfiles físicos exactamente duplicados",
        },
        {
            "control": "variables_sin_variacion",
            "estado": "OK" if int(matriz.nunique().le(1).sum()) == 0 else "ERROR",
            "valor": int(matriz.nunique().le(1).sum()),
            "umbral": "0",
            "detalle": "Variables que no separan ninguna ruta",
        },
        {
            "control": "correlacion_maxima_spearman",
            "estado": "REVISAR" if maxima_correlacion >= 0.85 else "OK",
            "valor": round(float(maxima_correlacion), 3),
            "umbral": "<0.85 preferible",
            "detalle": f"Par más asociado: {variable_a} y {variable_b}",
        },
    ]
    tabla = pd.DataFrame(controles)
    tabla.to_csv(SALIDA, index=False, encoding="utf-8")

    listo = (
        len(elegibles) >= MINIMO_RUTAS
        and not tabla["estado"].isin(["ERROR", "BLOQUEADO"]).any()
    )
    faltantes = max(0, MINIMO_RUTAS - len(elegibles))
    lineas = [
        "# Diagnóstico de preparación para el modelo",
        "",
        f"**Fecha:** {fecha}",
        f"**Estado:** {'LISTO PARA EVALUAR K-MEANS' if listo else 'NO LISTO PARA EL ENTRENAMIENTO FINAL'}",
        "",
        "## Resultado",
        "",
        f"El conjunto contiene **{len(elegibles)} rutas elegibles** de {len(dataset)} procesadas. "
        f"Faltan **{faltantes}** alternativas elegibles para la meta mínima de {MINIMO_RUTAS}.",
        "",
        "| Control | Estado | Valor | Umbral | Detalle |",
        "|---|---|---:|---|---|",
    ]
    for fila in tabla.itertuples(index=False):
        lineas.append(
            f"| {fila.control} | {fila.estado} | {fila.valor} | {fila.umbral} | {fila.detalle} |"
        )
    lineas.extend(
        [
            "",
            "## Decisión automática",
            "",
            "El script no entrena ni guarda K-means mientras la muestra mínima esté bloqueada. "
            "La correlación alta se registra para revisar redundancia, pero no elimina variables automáticamente.",
            "",
            "## Próximo paso",
            "",
            (
                "La meta mínima está alcanzada. Repetir EDA y evaluar valores de `k`, silueta, tamaño de grupos, "
                "estabilidad por semillas, sensibilidad a rutas cortas y concordancia con Ward; documentar la decisión "
                "antes de crear niveles o habilitar recomendaciones."
                if listo else
                "Añadir rutas completas y comparables. Al alcanzar el umbral se repetirá el EDA y se evaluarán "
                "valores de `k`, silueta, tamaño de grupos, estabilidad por semillas y concordancia con Ward."
            ),
            "",
        ]
    )
    informe.write_text("\n".join(lineas), encoding="utf-8")
    print(f"Rutas elegibles: {len(elegibles)}")
    print(f"Faltantes para el mínimo: {faltantes}")
    print(f"Estado: {'LISTO' if listo else 'BLOQUEADO'}")
    print(f"Correlación máxima absoluta: {maxima_correlacion:.3f}")


if __name__ == "__main__":
    main()
