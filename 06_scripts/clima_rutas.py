"""Condiciones meteorológicas actuales estimadas para dos puntos de una ruta.

Open-Meteo aporta resultados de modelo, no mediciones in situ. Esta consulta es
informativa y no interviene en la elegibilidad ni en una recomendación.
"""

from __future__ import annotations

import math

import requests

API = "https://api.open-meteo.com/v1/forecast"
VARIABLES = "temperature_2m,precipitation,weather_code,wind_speed_10m"


class ClimaNoDisponible(Exception):
    """La fuente externa no pudo entregar datos actuales utilizables."""


def puntos_consulta(perfil: list[dict], circular: bool = False) -> list[dict]:
    """Inicio y destino; en circuitos, inicio y punto más alto del trazado."""
    if len(perfil) < 2:
        raise ValueError("El perfil necesita al menos dos puntos")
    primero = perfil[0]
    segundo = max(perfil[1:], key=lambda p: p["elev"]) if circular else perfil[-1]
    puntos = [
        {"nombre": "Inicio", "lat": primero["lat"], "lon": primero["lon"], "elev": primero["elev"]},
        {"nombre": "Punto más alto" if circular else "Llegada", "lat": segundo["lat"],
         "lon": segundo["lon"], "elev": segundo["elev"]},
    ]
    for p in puntos:
        if not all(math.isfinite(float(p[k])) for k in ("lat", "lon", "elev")):
            raise ValueError("Coordenadas o elevación no finitas")
        if not -90 <= p["lat"] <= 90 or not -180 <= p["lon"] <= 180:
            raise ValueError("Coordenadas fuera de rango")
    return puntos


def descripcion(codigo: int) -> str:
    if codigo == 0:
        return "Despejado"
    if codigo in (1, 2, 3):
        return "Nubosidad variable"
    if codigo in (45, 48):
        return "Niebla"
    if codigo in (51, 53, 55, 56, 57):
        return "Llovizna"
    if codigo in (61, 63, 65, 66, 67, 80, 81, 82):
        return "Lluvia"
    if codigo in (71, 73, 75, 77, 85, 86):
        return "Nieve"
    if codigo in (95, 96, 99):
        return "Tormenta"
    return "Condición no especificada"


def consultar(perfil: list[dict], circular: bool = False, obtener=requests.get) -> list[dict]:
    """Consulta dos puntos en una llamada, con elevación DEM para ajuste del modelo."""
    puntos = puntos_consulta(perfil, circular)
    parametros = {
        "latitude": ",".join(f"{p['lat']:.6f}" for p in puntos),
        "longitude": ",".join(f"{p['lon']:.6f}" for p in puntos),
        "elevation": ",".join(f"{p['elev']:.0f}" for p in puntos),
        "current": VARIABLES,
        "timezone": "America/Guayaquil",
        "forecast_days": "1",
    }
    try:
        respuesta = obtener(API, params=parametros, timeout=8,
                           headers={"User-Agent": "tesis-trekking-pichincha/1.0"})
        respuesta.raise_for_status()
        datos = respuesta.json()
        if not isinstance(datos, list) or len(datos) != 2:
            raise ValueError("La API no devolvió ambos puntos")
        salida = []
        for punto, dato in zip(puntos, datos):
            actual = dato["current"]
            valores = {k: float(actual[k]) for k in ("temperature_2m", "precipitation", "wind_speed_10m")}
            if not all(math.isfinite(v) for v in valores.values()):
                raise ValueError("Valores meteorológicos no finitos")
            salida.append({
                **punto,
                "hora_local": str(actual["time"]),
                "temperatura_c": valores["temperature_2m"],
                "precipitacion_mm": valores["precipitation"],
                "viento_kmh": valores["wind_speed_10m"],
                "condicion": descripcion(int(actual["weather_code"])),
            })
        return salida
    except (requests.RequestException, TimeoutError, OSError, ValueError, KeyError, TypeError) as error:
        raise ClimaNoDisponible("No se pudo consultar el clima en este momento") from error
