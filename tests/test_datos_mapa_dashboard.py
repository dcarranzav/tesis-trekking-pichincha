import importlib.util
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

import gpxpy


MODULO = Path(__file__).resolve().parents[1] / "06_scripts" / "datos_mapa_dashboard.py"
spec = importlib.util.spec_from_file_location("datos_mapa_dashboard", MODULO)
mapa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mapa)


class TestDatosMapaDashboard(unittest.TestCase):
    def test_trazados_de_todas_las_rutas_elegibles(self):
        elegibles = [r for r in mapa.cargar_catalogo() if r["estado_modelado"] == "elegible_actual"]
        self.assertTrue(elegibles)
        for ruta in elegibles:
            with self.subTest(ruta=ruta["id_ruta"]):
                datos, puntos = mapa.cargar_trazado(ruta["id_ruta"])
                self.assertEqual(datos["features"][0]["properties"]["id_ruta"], ruta["id_ruta"])
                self.assertGreaterEqual(len(puntos), 2)

    def test_gpx_contiene_track_sin_alturas_inventadas(self):
        _, puntos = mapa.cargar_trazado("R023")
        contenido = mapa.gpx_desde_puntos("R023", "Cascada Guagrapamba", puntos)
        raiz = ET.fromstring(contenido)
        ns = {"g": "http://www.topografix.com/GPX/1/1"}
        trackpoints = raiz.findall(".//g:trkpt", ns)
        self.assertEqual(len(trackpoints), len(puntos))
        self.assertEqual(float(trackpoints[0].attrib["lat"]), puntos[0][0])
        self.assertIsNone(trackpoints[0].find("g:ele", ns))
        self.assertEqual(len(gpxpy.parse(contenido.decode("utf-8")).tracks[0].segments[0].points), len(puntos))

    def test_no_acepta_identificador_arbitrario(self):
        with self.assertRaises(ValueError):
            mapa.ruta_trazado("../inventario")

    def test_rechaza_geojson_sin_linea_valida(self):
        with tempfile.TemporaryDirectory(dir=mapa.RAIZ) as carpeta:
            archivo = Path(carpeta) / "R999_trazado_ida_2026-10-21.geojson"
            archivo.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                mapa.cargar_trazado("R999", Path(carpeta))

    def test_recorrido_simulado_vuelve_al_inicio(self):
        puntos = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]
        self.assertEqual(
            mapa.recorrido_para_animacion(puntos, circular=False),
            [puntos[0], puntos[1], puntos[2], puntos[1], puntos[0]],
        )
        self.assertEqual(mapa.recorrido_para_animacion(puntos, circular=True), puntos)


if __name__ == "__main__":
    unittest.main()
