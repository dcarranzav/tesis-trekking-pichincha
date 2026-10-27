"""El clima es informativo; la página debe tolerar fallas de la API."""

import sys
import unittest
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "06_scripts"))
import clima_rutas as clima


PERFIL = [
    {"lat": -0.1, "lon": -78.5, "elev": 3000.0},
    {"lat": -0.11, "lon": -78.51, "elev": 3200.0},
    {"lat": -0.12, "lon": -78.52, "elev": 3100.0},
]


class Respuesta:
    def __init__(self, datos):
        self.datos = datos

    def raise_for_status(self):
        return None

    def json(self):
        return self.datos


class ClimaRutas(unittest.TestCase):
    def test_puntos_ida_y_circuito(self):
        self.assertEqual(clima.puntos_consulta(PERFIL)[1]["nombre"], "Llegada")
        self.assertEqual(clima.puntos_consulta(PERFIL, circular=True)[1]["elev"], 3200.0)

    def test_coordenadas_invalidas(self):
        with self.assertRaises(ValueError):
            clima.puntos_consulta([PERFIL[0], {**PERFIL[1], "lat": 999}])

    def test_consulta_dos_puntos_y_elevaciones(self):
        capturado = {}
        datos = [{"current": {"time": "2026-10-22T18:00", "temperature_2m": 9.5,
                              "precipitation": 0.0, "wind_speed_10m": 12.0, "weather_code": 3}}] * 2

        def obtener(url, params, timeout, headers):
            capturado["url"] = url
            capturado["params"] = params
            capturado["timeout"] = timeout
            return Respuesta(datos)

        salida = clima.consultar(PERFIL, obtener=obtener)
        parametros = capturado["params"]
        self.assertEqual(parametros["elevation"], "3000,3100")
        self.assertEqual(parametros["timezone"], "America/Guayaquil")
        self.assertEqual(capturado["timeout"], 8)
        self.assertEqual([s["nombre"] for s in salida], ["Inicio", "Llegada"])
        self.assertEqual(salida[0]["condicion"], "Nubosidad variable")

    def test_falla_externa_no_sustituye_datos(self):
        def obtener(*_args, **_kwargs):
            raise requests.ConnectionError("sin conexión")

        with self.assertRaises(clima.ClimaNoDisponible):
            clima.consultar(PERFIL, obtener=obtener)

    def test_respuesta_incompleta(self):
        with self.assertRaises(clima.ClimaNoDisponible):
            clima.consultar(PERFIL, obtener=lambda *_a, **_k: Respuesta([]))


if __name__ == "__main__":
    unittest.main()
