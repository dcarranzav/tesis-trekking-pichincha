"""Clasificación reproducible de dificultad física estimada en tres niveles.

La regla adapta la dimensión ``cantidad de esfuerzo`` de MIDE a los datos
disponibles del proyecto. No afirma aplicar el MIDE completo: no calcula la
severidad del medio, la orientación ni la dificultad técnica.

Uso:
    python 06_scripts/clasificar_dificultad_fisica.py --fecha 2026-10-23
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
TABLAS = RAIZ / "07_resultados" / "tablas"
PERFILES = RAIZ / "04_datos_procesados" / "perfiles"
PERFILES_RAW = RAIZ / "03_datos_intermedios" / "elevacion"

VELOCIDAD_HORIZONTAL_KMH = 4.0
VELOCIDAD_SUBIDA_M_H = 400.0
VELOCIDAD_BAJADA_M_H = 600.0
UMBRAL_FACIL_H = 1.0
UMBRAL_MODERADA_H = 3.0
VERSION = "dificultad-fisica-mide-adaptada-3niv-v1"
FUENTE_MIDE = "https://montanasegura.com/MIDE/manualMIDE.pdf"


def mediana_centrada(valores: np.ndarray, ventana: int) -> np.ndarray:
    """Mediana centrada con extremos conservados, igual que el pipeline DEM."""
    if ventana < 3 or ventana % 2 == 0:
        raise ValueError("La ventana debe ser impar y al menos 3")
    radio = ventana // 2
    salida = np.array(
        [np.median(valores[max(0, i - radio): i + radio + 1]) for i in range(len(valores))],
        dtype=float,
    )
    salida[0], salida[-1] = valores[0], valores[-1]
    return salida


def desniveles_recorrido(elevacion: np.ndarray, tipo_recorrido: str) -> tuple[float, float]:
    """Devuelve desnivel positivo y negativo del recorrido completo."""
    elevacion = np.asarray(elevacion, dtype=float)
    if len(elevacion) < 2 or not np.isfinite(elevacion).all():
        raise ValueError("El perfil necesita al menos dos elevaciones finitas")
    cambio = np.diff(elevacion)
    subida_ida = float(cambio[cambio > 0].sum())
    bajada_ida = float(-cambio[cambio < 0].sum())
    if tipo_recorrido == "ida_y_vuelta":
        total = subida_ida + bajada_ida
        return total, total
    if tipo_recorrido == "circular":
        return subida_ida, bajada_ida
    raise ValueError(f"Tipo de recorrido no compatible: {tipo_recorrido}")


def horas_marcha_efectiva(
    distancia_km: float,
    subida_m: float,
    bajada_m: float,
    velocidad_horizontal_kmh: float = VELOCIDAD_HORIZONTAL_KMH,
) -> tuple[float, float, float]:
    """Horas MIDE adaptadas: mayor de horizontal/desnivel más la mitad del menor."""
    valores = np.asarray([distancia_km, subida_m, bajada_m, velocidad_horizontal_kmh], dtype=float)
    if not np.isfinite(valores).all() or np.any(valores[:3] < 0) or velocidad_horizontal_kmh <= 0:
        raise ValueError("Distancia, desniveles y velocidad deben ser finitos y no negativos")
    horizontal = float(distancia_km / velocidad_horizontal_kmh)
    desnivel = float(subida_m / VELOCIDAD_SUBIDA_M_H + bajada_m / VELOCIDAD_BAJADA_M_H)
    total = max(horizontal, desnivel) + 0.5 * min(horizontal, desnivel)
    return horizontal, desnivel, total


def nivel_por_horas(horas: float) -> tuple[int, str]:
    """Tres categorías solicitadas, basadas en los dos primeros cortes MIDE."""
    if not np.isfinite(horas) or horas < 0:
        raise ValueError("Las horas deben ser un valor finito no negativo")
    if horas <= UMBRAL_FACIL_H:
        return 1, "Fácil"
    if horas <= UMBRAL_MODERADA_H:
        return 2, "Moderada"
    return 3, "Difícil"


def cargar_muestra(ruta: Path | None = None) -> pd.DataFrame:
    ruta = ruta or TABLAS / "dataset_clasificacion_rutas.csv"
    datos = pd.read_csv(ruta)
    datos = datos.loc[datos["estado_modelado"].eq("elegible_actual")].sort_values("id_ruta").reset_index(drop=True)
    requeridas = {"id_ruta", "nombre_ruta", "tipo_recorrido", "distancia_total_km", "archivo_perfil"}
    if not requeridas.issubset(datos.columns) or datos.empty or not datos["id_ruta"].is_unique:
        raise ValueError("La muestra elegible no tiene la estructura requerida")
    if not np.isfinite(pd.to_numeric(datos["distancia_total_km"], errors="coerce")).all():
        raise ValueError("La distancia contiene valores no numéricos")
    return datos


def elevaciones(fila, variante: str = "mediana3") -> np.ndarray:
    procesado = PERFILES / fila.archivo_perfil
    if variante == "mediana3":
        tabla = pd.read_csv(procesado)
        return tabla["elevacion_mediana3_m"].to_numpy(float)
    crudo = PERFILES_RAW / fila.archivo_perfil.replace("procesado", "raw")
    valores = pd.read_csv(crudo)["elevacion_m"].to_numpy(float)
    if variante == "mediana5":
        return mediana_centrada(valores, 5)
    if variante == "crudo":
        return valores
    raise ValueError(f"Variante de elevación desconocida: {variante}")


def clasificar(datos: pd.DataFrame, velocidad_horizontal_kmh: float = VELOCIDAD_HORIZONTAL_KMH,
               variante_elevacion: str = "mediana3") -> pd.DataFrame:
    filas = []
    for fila in datos.itertuples(index=False):
        subida, bajada = desniveles_recorrido(elevaciones(fila, variante_elevacion), fila.tipo_recorrido)
        h_horizontal, h_desnivel, h_total = horas_marcha_efectiva(
            float(fila.distancia_total_km), subida, bajada, velocidad_horizontal_kmh
        )
        orden, nivel = nivel_por_horas(h_total)
        filas.append({
            "id_ruta": fila.id_ruta,
            "nombre_ruta": fila.nombre_ruta,
            "id_destino": fila.id_destino,
            "nombre_destino": fila.nombre_destino,
            "tipo_recorrido": fila.tipo_recorrido,
            "distancia_total_km": round(float(fila.distancia_total_km), 3),
            "desnivel_positivo_total_m": round(subida, 3),
            "desnivel_negativo_total_m": round(bajada, 3),
            "horas_componente_horizontal": round(h_horizontal, 4),
            "horas_componente_desnivel": round(h_desnivel, 4),
            "horas_marcha_efectiva_estimadas": round(h_total, 4),
            "nivel_orden": orden,
            "dificultad_fisica_estimada": nivel,
            "metodo": VERSION,
            "advertencia": (
                "Categoría de esfuerzo físico estimado; no evalúa dificultad técnica, orientación, "
                "estado, acceso, clima, seguridad ni aptitud personal"
            ),
        })
    return pd.DataFrame(filas).sort_values(["nivel_orden", "horas_marcha_efectiva_estimadas", "id_ruta"]).reset_index(drop=True)


def sensibilidad(datos: pd.DataFrame, base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    escenarios = (
        ("base_senda_4_kmh_mediana3", 4.0, "mediana3"),
        ("piso_desfavorable_3_kmh", 3.0, "mediana3"),
        ("piso_favorable_5_kmh", 5.0, "mediana3"),
        ("dem_mediana5", 4.0, "mediana5"),
        ("dem_crudo", 4.0, "crudo"),
    )
    base_nivel = base.set_index("id_ruta")["dificultad_fisica_estimada"]
    filas = []
    por_ruta = {ruta: [] for ruta in base_nivel.index}
    for nombre, velocidad, variante in escenarios:
        tabla = clasificar(datos, velocidad, variante).set_index("id_ruta")
        for ruta in base_nivel.index:
            nivel = tabla.loc[ruta, "dificultad_fisica_estimada"]
            cambia = nivel != base_nivel[ruta]
            filas.append({
                "escenario": nombre,
                "velocidad_horizontal_kmh": velocidad,
                "perfil_elevacion": variante,
                "id_ruta": ruta,
                "horas_estimadas": tabla.loc[ruta, "horas_marcha_efectiva_estimadas"],
                "nivel": nivel,
                "nivel_base": base_nivel[ruta],
                "cambia_frente_base": "si" if cambia else "no",
            })
            if cambia and nombre != "base_senda_4_kmh_mediana3":
                por_ruta[ruta].append(nombre)
    detalle = pd.DataFrame(filas)
    resumen = base[["id_ruta"]].copy()
    resumen["sensible_a_supuestos"] = resumen["id_ruta"].map(lambda r: "si" if por_ruta[r] else "no")
    resumen["escenarios_cambio"] = resumen["id_ruta"].map(lambda r: "|".join(por_ruta[r]))
    return detalle, resumen


def resumen_clases(tabla: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for orden, nivel in ((1, "Fácil"), (2, "Moderada"), (3, "Difícil")):
        grupo = tabla.loc[tabla["dificultad_fisica_estimada"].eq(nivel)]
        filas.append({
            "nivel_orden": orden,
            "dificultad_fisica_estimada": nivel,
            "n_rutas": len(grupo),
            "horas_min": round(float(grupo["horas_marcha_efectiva_estimadas"].min()), 3) if len(grupo) else "",
            "horas_max": round(float(grupo["horas_marcha_efectiva_estimadas"].max()), 3) if len(grupo) else "",
            "distancia_min_km": round(float(grupo["distancia_total_km"].min()), 3) if len(grupo) else "",
            "distancia_max_km": round(float(grupo["distancia_total_km"].max()), 3) if len(grupo) else "",
            "criterio": "<=1 h" if orden == 1 else (">1 y <=3 h" if orden == 2 else ">3 h"),
        })
    return pd.DataFrame(filas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", required=True)
    fecha = date.fromisoformat(parser.parse_args().fecha).isoformat()
    datos = cargar_muestra()
    if len(datos) != 20:
        raise ValueError(f"La clasificación vigente espera 20 rutas elegibles, no {len(datos)}")
    base = clasificar(datos)
    detalle_sens, resumen_sens = sensibilidad(datos, base)
    base = base.merge(resumen_sens, on="id_ruta", how="left", validate="one_to_one")
    resumen = resumen_clases(base)

    salida = TABLAS / f"clasificacion_dificultad_fisica_{fecha}.csv"
    base.to_csv(salida, index=False, encoding="utf-8")
    resumen.to_csv(TABLAS / f"clasificacion_dificultad_fisica_resumen_{fecha}.csv", index=False, encoding="utf-8")
    detalle_sens.to_csv(TABLAS / f"clasificacion_dificultad_fisica_sensibilidad_{fecha}.csv", index=False, encoding="utf-8")
    parametros = {
        "version": VERSION,
        "fecha": fecha,
        "n_rutas": len(base),
        "regla": "max(distancia/4, subida/400 + bajada/600) + 0.5*min(distancia/4, subida/400 + bajada/600)",
        "parametros": {
            "velocidad_horizontal_kmh": VELOCIDAD_HORIZONTAL_KMH,
            "velocidad_subida_m_h": VELOCIDAD_SUBIDA_M_H,
            "velocidad_bajada_m_h": VELOCIDAD_BAJADA_M_H,
            "facil_hasta_h": UMBRAL_FACIL_H,
            "moderada_hasta_h": UMBRAL_MODERADA_H,
            "dificil_desde_h_mayor_que": UMBRAL_MODERADA_H,
        },
        "adaptacion": "MIDE 1 -> Fácil; MIDE 2 -> Moderada; MIDE 3-5 -> Difícil",
        "fuente_principal": FUENTE_MIDE,
        "alcance": "Solo cantidad de esfuerzo físico estimado; no es MIDE completo ni recomendación de salida",
        "sha256_dataset": hashlib.sha256((TABLAS / "dataset_clasificacion_rutas.csv").read_bytes()).hexdigest(),
        "archivo_clasificacion": salida.name,
        "sha256_clasificacion": hashlib.sha256(salida.read_bytes()).hexdigest(),
    }
    (TABLAS / f"clasificacion_dificultad_fisica_parametros_{fecha}.json").write_text(
        json.dumps(parametros, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(base[["id_ruta", "horas_marcha_efectiva_estimadas", "dificultad_fisica_estimada",
                "sensible_a_supuestos"]].to_string(index=False))
    print("\n", resumen.to_string(index=False))


if __name__ == "__main__":
    main()
