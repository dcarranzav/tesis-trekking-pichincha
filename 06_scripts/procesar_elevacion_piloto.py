"""Filtra los perfiles del piloto y calcula indicadores de elevación."""

from pathlib import Path

import numpy as np
import pandas as pd


FECHA = "2026-10-05"
RUTAS = ("R001", "R003", "R005", "R006")


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def mediana_centrada(valores: np.ndarray, ventana: int) -> np.ndarray:
    radio = ventana // 2
    resultado = np.array(
        [
            np.median(
                valores[max(0, i - radio) : min(len(valores), i + radio + 1)]
            )
            for i in range(len(valores))
        ],
        dtype=float,
    )
    resultado[0] = valores[0]
    resultado[-1] = valores[-1]
    return resultado


def indicadores(elevacion: np.ndarray, distancias: np.ndarray) -> dict:
    cambio_elevacion = np.diff(elevacion)
    cambio_distancia = np.diff(distancias)
    pendientes = cambio_elevacion / cambio_distancia * 100
    ascenso_ida = float(cambio_elevacion[cambio_elevacion > 0].sum())
    descenso_ida = float(-cambio_elevacion[cambio_elevacion < 0].sum())
    return {
        "elevacion_min_m": float(elevacion.min()),
        "elevacion_max_m": float(elevacion.max()),
        "ascenso_ida_m": ascenso_ida,
        "descenso_ida_m": descenso_ida,
        "ascenso_ida_vuelta_m": ascenso_ida + descenso_ida,
        "pendiente_media_abs_pct": float(
            np.abs(cambio_elevacion).sum() / cambio_distancia.sum() * 100
        ),
        "pendiente_p95_abs_pct": float(np.percentile(np.abs(pendientes), 95)),
        "pendiente_max_abs_pct": float(np.abs(pendientes).max()),
    }


proyecto = localizar_proyecto()
carpeta_raw = proyecto / "03_datos_intermedios" / "elevacion"
carpeta_procesada = proyecto / "04_datos_procesados" / "perfiles"
carpeta_resultados = proyecto / "07_resultados" / "tablas"
carpeta_procesada.mkdir(parents=True, exist_ok=True)
carpeta_resultados.mkdir(parents=True, exist_ok=True)

resumen = []
sensibilidad = []
tramos_extremos = []

for id_ruta in RUTAS:
    archivo_raw = carpeta_raw / f"{id_ruta}_perfil_elevacion_raw_{FECHA}.csv"
    perfil = pd.read_csv(archivo_raw)
    elevacion_raw = perfil["elevacion_m"].to_numpy(float)
    distancias = perfil["distancia_m"].to_numpy(float)
    elevacion_mediana3 = mediana_centrada(elevacion_raw, 3)
    elevacion_mediana5 = mediana_centrada(elevacion_raw, 5)

    perfil["elevacion_mediana3_m"] = np.round(elevacion_mediana3, 3)
    perfil["cambio_elevacion_m"] = np.round(
        np.insert(np.diff(elevacion_mediana3), 0, np.nan), 3
    )
    perfil["pendiente_pct"] = np.round(
        np.insert(
            np.diff(elevacion_mediana3) / np.diff(distancias) * 100,
            0,
            np.nan,
        ),
        3,
    )
    perfil["metodo_filtrado"] = "mediana_centrada_3_puntos_extremos_conservados"

    indices_extremos = (
        perfil["pendiente_pct"].abs().nlargest(5).index.tolist()
    )
    for indice in indices_extremos:
        tramos_extremos.append(
            {
                "id_ruta": id_ruta,
                "orden_fin": int(perfil.loc[indice, "orden"]),
                "distancia_inicio_m": float(perfil.loc[indice - 1, "distancia_m"]),
                "distancia_fin_m": float(perfil.loc[indice, "distancia_m"]),
                "elevacion_inicio_m": float(elevacion_mediana3[indice - 1]),
                "elevacion_fin_m": float(elevacion_mediana3[indice]),
                "cambio_elevacion_m": float(perfil.loc[indice, "cambio_elevacion_m"]),
                "pendiente_pct": float(perfil.loc[indice, "pendiente_pct"]),
                "longitud_fin": float(perfil.loc[indice, "longitud"]),
                "latitud_fin": float(perfil.loc[indice, "latitud"]),
            }
        )

    archivo_procesado = (
        carpeta_procesada
        / f"{id_ruta}_perfil_elevacion_procesado_{FECHA}.csv"
    )
    perfil.to_csv(archivo_procesado, index=False, encoding="utf-8")

    principal = indicadores(elevacion_mediana3, distancias)
    resumen.append(
        {
            "id_ruta": id_ruta,
            "distancia_ida_km": distancias[-1] / 1000,
            "distancia_ida_vuelta_km": distancias[-1] * 2 / 1000,
            "puntos_perfil": len(perfil),
            "valores_faltantes": int(perfil["elevacion_m"].isna().sum()),
            "metodo_principal": "mediana_centrada_3_puntos_extremos_conservados",
            **principal,
        }
    )

    for metodo, elevacion in (
        ("raw", elevacion_raw),
        ("mediana_3", elevacion_mediana3),
        ("mediana_5", elevacion_mediana5),
    ):
        sensibilidad.append(
            {
                "id_ruta": id_ruta,
                "metodo": metodo,
                **indicadores(elevacion, distancias),
            }
        )

resumen_df = pd.DataFrame(resumen).round(3)
sensibilidad_df = pd.DataFrame(sensibilidad).round(3)
tramos_extremos_df = pd.DataFrame(tramos_extremos).round(6)

archivo_resumen = carpeta_resultados / "indicadores_elevacion_piloto.csv"
archivo_sensibilidad = carpeta_resultados / "sensibilidad_elevacion_piloto.csv"
archivo_tramos = carpeta_resultados / "tramos_pendiente_extrema_piloto.csv"
resumen_df.to_csv(archivo_resumen, index=False, encoding="utf-8")
sensibilidad_df.to_csv(archivo_sensibilidad, index=False, encoding="utf-8")
tramos_extremos_df.to_csv(archivo_tramos, index=False, encoding="utf-8")

assert len(resumen_df) == 4
assert resumen_df["valores_faltantes"].eq(0).all()
assert resumen_df["elevacion_max_m"].gt(resumen_df["elevacion_min_m"]).all()
assert resumen_df["ascenso_ida_vuelta_m"].gt(0).all()
assert len(sensibilidad_df) == 12
assert len(tramos_extremos_df) == 20

print("Perfiles procesados:", len(resumen_df))
print("Valores faltantes:", int(resumen_df["valores_faltantes"].sum()))
print("Método principal: mediana centrada de 3 puntos con extremos conservados")
print("\nIndicadores principales:")
print(resumen_df.to_string(index=False))
print("\nArchivos guardados:")
print(archivo_resumen.name)
print(archivo_sensibilidad.name)
print(archivo_tramos.name)
