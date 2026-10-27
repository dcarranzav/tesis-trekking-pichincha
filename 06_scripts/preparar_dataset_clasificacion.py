"""Unifica inventario e indicadores físicos para la futura clasificación."""

from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
DOCUMENTACION = RAIZ / "01_documentacion"
PERFILES = RAIZ / "04_datos_procesados" / "perfiles"
TABLAS = RAIZ / "07_resultados" / "tablas"


def cargar_indicadores() -> pd.DataFrame:
    piloto = pd.read_csv(TABLAS / "indicadores_elevacion_piloto.csv")
    ampliacion = pd.read_csv(TABLAS / "indicadores_elevacion_ampliacion.csv")

    piloto_normalizado = piloto.assign(
        tipo_recorrido="ida_y_vuelta",
        distancia_trazado_km=piloto["distancia_ida_km"],
        distancia_total_km=piloto["distancia_ida_vuelta_km"],
        ascenso_total_m=piloto["ascenso_ida_vuelta_m"],
        ascenso_trazado_m=piloto["ascenso_ida_m"],
        descenso_trazado_m=piloto["descenso_ida_m"],
        desnivel_acumulado_trazado_m=(
            piloto["ascenso_ida_m"] + piloto["descenso_ida_m"]
        ),
        archivo_dem="Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif",
    )

    columnas = list(ampliacion.columns)
    return pd.concat([piloto_normalizado[columnas], ampliacion], ignore_index=True)


def calcular_elevacion_media() -> pd.DataFrame:
    filas = []
    for archivo in sorted(PERFILES.glob("R*_perfil_elevacion_procesado_*.csv")):
        perfil = pd.read_csv(archivo)
        ids = perfil["id_ruta"].dropna().unique()
        assert len(ids) == 1, f"Perfil con identificadores ambiguos: {archivo.name}"
        filas.append(
            {
                "id_ruta": ids[0],
                "elevacion_media_m": perfil["elevacion_mediana3_m"].mean(),
                "archivo_perfil": archivo.name,
            }
        )
    return pd.DataFrame(filas)


def main() -> None:
    inventario = pd.read_csv(DOCUMENTACION / "inventario_rutas.csv")
    indicadores = cargar_indicadores()
    medias = calcular_elevacion_media()

    assert inventario["id_ruta"].is_unique
    assert inventario.groupby("id_destino")["nombre_destino"].nunique().eq(1).all(), (
        "Un mismo id_destino tiene nombres de destino distintos"
    )
    assert indicadores["id_ruta"].is_unique
    assert set(inventario["id_ruta"]) == set(indicadores["id_ruta"])
    assert set(inventario["id_ruta"]) == set(medias["id_ruta"])

    dataset = inventario.merge(indicadores, on="id_ruta", validate="one_to_one")
    dataset = dataset.merge(medias, on="id_ruta", validate="one_to_one")

    dataset["estado_modelado"] = "no_elegible_aun"
    elegible = (
        dataset["calidad_preliminar"].eq("apta")
        & dataset["comparable_trekking"].eq("si")
        & dataset["requiere_equipo_tecnico"].eq("no")
        & dataset["decision"].isin(["pendiente", "incluir"])
        & dataset["valores_faltantes"].eq(0)
    )
    dataset.loc[elegible, "estado_modelado"] = "elegible_actual"

    columnas_modelo = [
        "distancia_total_km",
        "ascenso_total_m",
        "elevacion_max_m",
        "pendiente_media_abs_pct",
        "pendiente_p95_abs_pct",
    ]
    assert not dataset[columnas_modelo].isna().any().any()
    assert (dataset["distancia_total_km"] > 0).all()
    assert (dataset["elevacion_max_m"] > dataset["elevacion_min_m"]).all()

    columnas_salida = [
        "id_ruta",
        "nombre_ruta",
        "id_destino",
        "nombre_destino",
        "nombre_variante",
        "canton",
        "sector",
        "tipo_recorrido_x",
        "actividad_declarada",
        "requiere_equipo_tecnico",
        "comparable_trekking",
        "calidad_preliminar",
        "decision",
        "estado_modelado",
        "distancia_trazado_km",
        "distancia_total_km",
        "ascenso_total_m",
        "elevacion_min_m",
        "elevacion_media_m",
        "elevacion_max_m",
        "pendiente_media_abs_pct",
        "pendiente_p95_abs_pct",
        "pendiente_max_abs_pct",
        "puntos_perfil",
        "valores_faltantes",
        "metodo_principal",
        "archivo_dem",
        "archivo_perfil",
    ]
    dataset = dataset[columnas_salida].rename(
        columns={"tipo_recorrido_x": "tipo_recorrido"}
    )
    dataset = dataset.sort_values("id_ruta").reset_index(drop=True)

    auditoria = dataset[
        [
            "id_ruta",
            "calidad_preliminar",
            "decision",
            "comparable_trekking",
            "requiere_equipo_tecnico",
            "valores_faltantes",
            "estado_modelado",
        ]
    ].copy()
    def definir_accion(fila: pd.Series) -> str:
        acciones = []
        if fila["calidad_preliminar"] == "dudosa":
            acciones.append("resolver_calidad_o_identidad")
        if fila["comparable_trekking"] == "por_verificar":
            acciones.append("verificar_compatibilidad_tematica")
        if fila["decision"] == "excluir_provisional":
            acciones.append("verificar_identidad_y_extremos")
        return "|".join(acciones) if acciones else "ninguna_para_dataset"

    auditoria["accion_pendiente"] = auditoria.apply(definir_accion, axis=1)

    TABLAS.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(TABLAS / "dataset_clasificacion_rutas.csv", index=False, float_format="%.3f")
    auditoria.to_csv(
        TABLAS / "auditoria_dataset_clasificacion.csv", index=False
    )

    print(f"Rutas unificadas: {len(dataset)}")
    elegibles_actuales = int(dataset["estado_modelado"].eq("elegible_actual").sum())
    print(f"Elegibles actuales: {elegibles_actuales}")
    print(f"Valores faltantes en variables modelo: {int(dataset[columnas_modelo].isna().sum().sum())}")
    if elegibles_actuales < 20:
        print("No se entrenó ningún modelo: la muestra elegible todavía es insuficiente.")
    else:
        print("No se entrenó ningún modelo: la meta de muestra se alcanzó; falta validar y aprobar el modelo final.")


if __name__ == "__main__":
    main()
