"""Ensaya el control de duplicados y la puerta de cierre del inventario.

El solapamiento a 20 m es una alerta geométrica, no una prueba de que dos
itinerarios turísticos sean la misma alternativa. No modifica elegibilidad.
"""

from argparse import ArgumentParser
from datetime import date
from pathlib import Path
import os
import re
import sys

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
TRAZADOS = RAIZ / "03_datos_intermedios" / "trazados"
TABLAS = RAIZ / "07_resultados" / "tablas"
DOCUMENTACION = RAIZ / "01_documentacion"
META = 20
BUFFER_M = 20
UMBRAL_DUPLICADO = 0.90
UMBRAL_TRAMO_COMPARTIDO = 0.65


def geometria_vigente(id_ruta: str):
    archivos = sorted(TRAZADOS.glob(f"{id_ruta}_trazado_*.geojson"))
    assert archivos, f"No se encontró trazado para {id_ruta}"
    fechas = {}
    for archivo in archivos:
        hallazgo = re.search(r"(\d{4}-\d{2}-\d{2})", archivo.name)
        fecha = hallazgo.group(1) if hallazgo else "0000-00-00"
        fechas.setdefault(fecha, []).append(archivo)
    actuales = fechas[max(fechas)]
    assert len(actuales) == 1, f"Ambigüedad de versión para {id_ruta}"
    gdf = gpd.read_file(actuales[0]).to_crs(32717)
    assert len(gdf) == 1 and gdf.geometry.iloc[0].geom_type == "LineString"
    return gdf.geometry.iloc[0]


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", required=True, help="Fecha real de ejecución (AAAA-MM-DD)")
    args = parser.parse_args()
    try:
        fecha = date.fromisoformat(args.fecha).isoformat()
    except ValueError as error:
        parser.error(f"Fecha inválida: {error}")

    inventario = pd.read_csv(DOCUMENTACION / "inventario_rutas.csv")
    dataset = pd.read_csv(TABLAS / "dataset_clasificacion_rutas.csv")
    assert inventario["id_ruta"].is_unique and dataset["id_ruta"].is_unique
    assert set(inventario["id_ruta"]) == set(dataset["id_ruta"])

    filas = dataset.sort_values("id_ruta").set_index("id_ruta")
    geometrias = {id_ruta: geometria_vigente(id_ruta) for id_ruta in filas.index}
    pares = []
    ids = list(filas.index)
    for indice, id_a in enumerate(ids):
        linea_a = geometrias[id_a]
        for id_b in ids[indice + 1 :]:
            linea_b = geometrias[id_b]
            cobertura_a = min(1.0, linea_a.intersection(linea_b.buffer(BUFFER_M)).length / linea_a.length)
            cobertura_b = min(1.0, linea_b.intersection(linea_a.buffer(BUFFER_M)).length / linea_b.length)
            pares.append(
                {
                    "id_ruta_a": id_a,
                    "id_ruta_b": id_b,
                    "mismo_destino": filas.loc[id_a, "id_destino"] == filas.loc[id_b, "id_destino"],
                    "distancia_minima_m": round(linea_a.distance(linea_b), 1),
                    "fraccion_a_cubierta_20m": round(cobertura_a, 3),
                    "fraccion_b_cubierta_20m": round(cobertura_b, 3),
                    "duplicado_potencial": cobertura_a >= UMBRAL_DUPLICADO and cobertura_b >= UMBRAL_DUPLICADO,
                    "tramo_compartido_relevante": (
                        filas.loc[id_a, "id_destino"] == filas.loc[id_b, "id_destino"]
                        and max(cobertura_a, cobertura_b) >= UMBRAL_TRAMO_COMPARTIDO
                    ),
                }
            )

    tabla = pd.DataFrame(pares)
    assert len(tabla) == len(ids) * (len(ids) - 1) // 2
    assert not tabla[["id_ruta_a", "id_ruta_b"]].duplicated().any()
    salida = TABLAS / f"solapamiento_rutas_{fecha}.csv"
    tabla.to_csv(salida, index=False)
    alertas = tabla.loc[tabla["duplicado_potencial"]]
    tramos_compartidos = tabla.loc[tabla["tramo_compartido_relevante"]]
    elegibles = int(filas["estado_modelado"].eq("elegible_actual").sum())
    no_elegibles = int(len(filas) - elegibles)
    faltantes = max(0, META - elegibles)
    cierre = elegibles >= META and alertas.empty

    lineas = [
        "# Ensayo anticipado del cierre de inventario previsto para el 16 de octubre" if fecha < "2026-10-16" else "# Control de cierre del inventario",
        "",
        f"**Fecha de ejecución:** {fecha}. **Resultado:** {'PASA CONTROLES AUTOMÁTICOS' if cierre else 'NO CONGELAR TODAVÍA'}.",
        "",
        "Este control no convierte rutas pendientes en elegibles. El cierre definitivo requiere también la revisión documental y temática descrita en la metodología.",
        "",
        "## Puerta cuantitativa",
        "",
        f"- Rutas procesadas: **{len(filas)}**; elegibles provisionales: **{elegibles}**; no elegibles: **{no_elegibles}**.",
        f"- Meta mínima: **{META}**; faltan **{faltantes}** alternativas elegibles.",
        f"- Pares geométricos comparados: **{len(tabla)}**; alertas de duplicado potencial: **{len(alertas)}**.",
        f"- Pares del mismo destino con un tramo compartido relevante: **{len(tramos_compartidos)}**.",
        "",
        "## Método del control espacial",
        "",
        f"Se proyectaron las {len(geometrias)} líneas vigentes a UTM 17S y se midió qué fracción de cada trazo queda dentro de un corredor de 20 m alrededor del otro. Se marca alerta solo cuando **ambas** fracciones son al menos 0.90. El umbral es de cribado: un acceso compartido puede producir una alerta sin que las rutas sean idénticas, y una ruta mal delimitada puede escapar al control. La tabla completa permite revisar todos los pares.",
        "",
    ]
    if not alertas.empty:
        lineas.extend(["## Pares que requieren revisión", ""])
        for fila in alertas.itertuples(index=False):
            lineas.append(
                f"- {fila.id_ruta_a}–{fila.id_ruta_b}: coberturas {fila.fraccion_a_cubierta_20m:.3f} y {fila.fraccion_b_cubierta_20m:.3f}."
            )
        lineas.append("")
    if not tramos_compartidos.empty:
        lineas.extend(["## Tramos compartidos para revisión de diversidad", ""])
        for fila in tramos_compartidos.itertuples(index=False):
            lineas.append(
                f"- {fila.id_ruta_a}–{fila.id_ruta_b}: coberturas {fila.fraccion_a_cubierta_20m:.3f} y {fila.fraccion_b_cubierta_20m:.3f}. No se marca como duplicado; revisar que los destinos finales y las diferencias físicas justifican dos alternativas."
            )
        lineas.append("")
    lineas.extend(
        [
            "## Decisión para el cronograma",
            "",
            "No se congela el inventario ni se entrena el modelo final mientras falten rutas elegibles o queden dudas sobre identidad, extremos, actividad o duplicidad. R012 y R014 continúan excluidas provisionalmente; R011 y R013 aún requieren validar el recorrido turístico completo. La siguiente incorporación exige geometrías nominales y verificables, no un aumento del conteo con fragmentos. Los ensayos K-means existentes son únicamente exploratorios.",
            "",
            f"Tabla reproducible: `07_resultados/tablas/{salida.name}`.",
            "",
        ]
    )
    (DOCUMENTACION / f"preparacion_cierre_inventario_{fecha}.md").write_text("\n".join(lineas), encoding="utf-8")
    print(f"Rutas: {len(filas)}; elegibles: {elegibles}; faltantes: {faltantes}")
    print(f"Pares: {len(tabla)}; alertas: {len(alertas)}; cierre: {'SI' if cierre else 'NO'}")


if __name__ == "__main__":
    main()
