"""Comparación por destino y contrato de recomendación para la interfaz futura.

No entrena un clasificador ni convierte números de clúster en dificultad.
Mientras falten clases interpretadas y aprobadas, solo permite comparar métricas.
"""

from dataclasses import dataclass
from pathlib import Path
from math import asin, cos, inf, radians, sin, sqrt
from typing import Collection, Mapping

import pandas as pd


class ModeloNoValidado(ValueError):
    """La muestra o la interpretación aún no autorizan recomendaciones."""


@dataclass(frozen=True)
class Preferencias:
    nivel_deseado: int
    distancia_max_km: float | None = None
    ascenso_max_m: float | None = None
    origen_lat_lon: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.nivel_deseado, int) or isinstance(self.nivel_deseado, bool) or self.nivel_deseado < 1:
            raise ValueError("El nivel deseado debe ser un ordinal positivo")
        for nombre in ("distancia_max_km", "ascenso_max_m"):
            valor = getattr(self, nombre)
            if valor is not None and (not 0 < valor < inf):
                raise ValueError(f"{nombre} debe ser positivo y finito")
        if self.origen_lat_lon is not None:
            lat, lon = self.origen_lat_lon
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Coordenadas de origen inválidas")


DESTINOS_EXACTOS = Path(__file__).resolve().parents[1] / "01_documentacion" / "destinos_exactos_interfaz.csv"


def cargar_destinos_exactos(ruta: Path = DESTINOS_EXACTOS) -> pd.DataFrame:
    """Mapeo ruta -> (lugar, destino exacto) que usa también la interfaz."""
    tabla = pd.read_csv(ruta, encoding="utf-8-sig", dtype=str)
    faltantes = {"lugar", "destino_exacto", "id_ruta"} - set(tabla.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas en el mapeo de destinos: {', '.join(sorted(faltantes))}")
    if tabla["id_ruta"].duplicated().any():
        raise ValueError("Una ruta no puede tener dos destinos exactos")
    return tabla[["id_ruta", "lugar", "destino_exacto"]]


def _con_destino_exacto(dataset: pd.DataFrame, destinos_exactos: pd.DataFrame) -> pd.DataFrame:
    """Añade lugar y destino exacto. Una ruta sin entrada queda sola: nunca se agrupa por suposición."""
    mapeo = destinos_exactos.set_index("id_ruta")
    resultado = dataset.copy()
    resultado["lugar"] = resultado["id_ruta"].map(mapeo["lugar"])
    resultado["destino_exacto"] = resultado["id_ruta"].map(mapeo["destino_exacto"])
    sin = resultado["destino_exacto"].isna()
    resultado.loc[sin, "lugar"] = resultado.loc[sin, "id_destino"]
    resultado.loc[sin, "destino_exacto"] = resultado.loc[sin, "id_ruta"] + " (destino exacto por definir)"
    return resultado


def alternativas_por_destino(
    dataset: pd.DataFrame,
    id_destino: str,
    destinos_exactos: pd.DataFrame | None = None,
    destino_exacto: str | None = None,
) -> pd.DataFrame:
    """Alternativas elegibles que llegan al MISMO destino final exacto; no produce una recomendación.

    `id_destino` es solo una categoría amplia para navegar (p. ej. Mindo). Si contiene varios destinos
    exactos, hay que indicar `destino_exacto`; si no, se rechaza para no mezclar, por ejemplo,
    Cascada Corazón, Mirador y Yellow House.
    """
    requeridas = {
        "id_ruta", "id_destino", "estado_modelado", "distancia_total_km",
        "ascenso_total_m", "elevacion_max_m", "pendiente_media_abs_pct",
    }
    faltantes = requeridas - set(dataset.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas: {', '.join(sorted(faltantes))}")
    if id_destino not in set(dataset["id_destino"]):
        raise ValueError(f"Destino desconocido: {id_destino}")
    destinos_exactos = cargar_destinos_exactos() if destinos_exactos is None else destinos_exactos
    rutas = _con_destino_exacto(
        dataset.loc[dataset["id_destino"].eq(id_destino) & dataset["estado_modelado"].eq("elegible_actual")],
        destinos_exactos,
    )
    if rutas["id_ruta"].duplicated().any():
        raise ValueError("Identificadores de ruta duplicados")
    disponibles = sorted(rutas["destino_exacto"].unique())
    if destino_exacto is None:
        if len(disponibles) > 1:
            raise ValueError(
                "El destino amplio tiene varios destinos exactos; indique destino_exacto: " + " | ".join(disponibles)
            )
    else:
        if destino_exacto not in disponibles:
            raise ValueError(f"Destino exacto desconocido o sin alternativas elegibles: {destino_exacto}")
        rutas = rutas.loc[rutas["destino_exacto"].eq(destino_exacto)]
    return rutas.sort_values("id_ruta").reset_index(drop=True)


def distancia_haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    for lat, lon in (a, b):
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Coordenadas inválidas para calcular cercanía")
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
    termino = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    return 2 * 6371.0088 * asin(min(1.0, sqrt(termino)))


def recomendar(
    alternativas: pd.DataFrame,
    preferencias: Preferencias,
    niveles_interpretados: Mapping[str, int] | None,
    *,
    version_modelo_final: str | None,
    inicios_lat_lon: Mapping[str, tuple[float, float]] | None = None,
    rutas_habilitadas: Collection[str] | None = None,
) -> list[dict]:
    """Ordena opciones solo con clases finales interpretadas, nunca con grupos crudos.

    Primero respeta límites físicos; luego ordena por cercanía al nivel deseado,
    distancia al inicio (si se conoce) y longitud. Requiere una lista externa
    de rutas cuya apertura y condiciones se hayan verificado; no evalúa
    seguridad por sí misma.
    """
    if not version_modelo_final or not version_modelo_final.strip() or not niveles_interpretados:
        raise ModeloNoValidado("Falta modelo final validado y niveles interpretados")
    if rutas_habilitadas is None:
        raise ModeloNoValidado("Falta validar apertura y condiciones de las rutas para recomendarlas")
    requeridas = {"id_ruta", "id_destino", "estado_modelado", "distancia_total_km", "ascenso_total_m"}
    faltantes = requeridas - set(alternativas.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas para recomendar: {', '.join(sorted(faltantes))}")
    if alternativas["id_ruta"].isna().any() or alternativas["id_ruta"].duplicated().any():
        raise ValueError("Identificadores de ruta vacíos o duplicados")
    if alternativas["id_destino"].nunique(dropna=False) > 1:
        raise ValueError("La comparación debe corresponder a un solo destino")
    if not alternativas["estado_modelado"].eq("elegible_actual").all():
        raise ModeloNoValidado("Hay rutas fuera del conjunto elegible en la comparación")
    if "destino_exacto" not in alternativas.columns:
        raise ValueError("Falta destino_exacto: obtenga las alternativas con alternativas_por_destino")
    if alternativas["destino_exacto"].isna().any() or alternativas["destino_exacto"].nunique() > 1:
        raise ValueError("No se pueden comparar ni recomendar alternativas con destinos finales distintos")
    habilitadas = set(rutas_habilitadas)
    if preferencias.origen_lat_lon is not None and inicios_lat_lon is None:
        raise ValueError("Faltan coordenadas de inicio para comparar cercanía")
    resultados = []
    for fila in alternativas.itertuples(index=False):
        if fila.id_ruta not in habilitadas:
            continue
        nivel = niveles_interpretados.get(fila.id_ruta)
        if not isinstance(nivel, int) or isinstance(nivel, bool) or nivel < 1:
            raise ModeloNoValidado(f"Falta nivel interpretado para {fila.id_ruta}")
        distancia = float(fila.distancia_total_km)
        ascenso = float(fila.ascenso_total_m)
        if not (0 < distancia < inf and 0 <= ascenso < inf):
            raise ValueError(f"Métricas físicas inválidas en {fila.id_ruta}")
        if preferencias.distancia_max_km is not None and distancia > preferencias.distancia_max_km:
            continue
        if preferencias.ascenso_max_m is not None and ascenso > preferencias.ascenso_max_m:
            continue
        cercania = None
        if preferencias.origen_lat_lon is not None:
            assert inicios_lat_lon is not None
            if fila.id_ruta not in inicios_lat_lon:
                raise ValueError(f"Falta inicio geográfico de {fila.id_ruta}")
            cercania = distancia_haversine_km(
                preferencias.origen_lat_lon, inicios_lat_lon[fila.id_ruta]
            )
        resultados.append(
            {
                "id_ruta": fila.id_ruta,
                "id_destino": fila.id_destino,
                "nivel_exigencia_ordinal": nivel,
                "distancia_total_km": distancia,
                "ascenso_total_m": ascenso,
                "distancia_origen_inicio_km": cercania,
                "diferencia_nivel": abs(nivel - preferencias.nivel_deseado),
                "criterio": "nivel deseado, cercanía al inicio y longitud; límites físicos aplicados",
                "version_modelo_final": version_modelo_final,
            }
        )
    return sorted(
        resultados,
        key=lambda r: (
            r["diferencia_nivel"],
            r["distancia_origen_inicio_km"] if r["distancia_origen_inicio_km"] is not None else inf,
            r["distancia_total_km"],
            r["id_ruta"],
        ),
    )
