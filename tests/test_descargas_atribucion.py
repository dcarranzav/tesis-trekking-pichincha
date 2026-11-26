"""Metadatos de procedencia y conservación de las 20 rutas descargables."""

import importlib.util
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

import gpxpy


MODULO = Path(__file__).resolve().parents[1] / "06_scripts" / "datos_mapa_dashboard.py"
spec = importlib.util.spec_from_file_location("datos_mapa_dashboard_descargas", MODULO)
mapa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mapa)
NS_URI = "http://www.topografix.com/GPX/1/1"
NS = {"g": NS_URI}


def nombres_hijos(elemento):
    return [hijo.tag.removeprefix(f"{{{NS_URI}}}") for hijo in elemento]


class TestDescargasAtribucion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rutas = [
            fila for fila in mapa.cargar_catalogo()
            if fila["estado_modelado"] == "elegible_actual"
        ]

    def test_hay_veinte_rutas_elegibles_unicas(self):
        self.assertEqual(len(self.rutas), 20)
        self.assertEqual(len({fila["id_ruta"] for fila in self.rutas}), 20)

    def test_gpx_metadatos_orden_y_geometria_de_cada_ruta(self):
        for fila in self.rutas:
            id_ruta = fila["id_ruta"]
            with self.subTest(ruta=id_ruta):
                _, puntos = mapa.cargar_trazado(id_ruta)
                contenido = mapa.gpx_desde_puntos(id_ruta, fila["nombre_ruta"], puntos)
                raiz = ET.fromstring(contenido)
                self.assertEqual(raiz.attrib["version"], "1.1")
                self.assertEqual(nombres_hijos(raiz), ["metadata", "trk"])
                meta, track = raiz
                self.assertEqual(nombres_hijos(meta), ["name", "desc", "copyright", "link"])
                self.assertEqual(nombres_hijos(track), ["name", "cmt", "trkseg"])
                self.assertIn(id_ruta, meta.findtext("g:name", namespaces=NS))
                descripcion = meta.findtext("g:desc", namespaces=NS)
                for texto in ("Datos © colaboradores de OpenStreetMap", "ODbL", "2D", "sin elevaciones ni tiempos"):
                    self.assertIn(texto, descripcion)
                derechos = meta.find("g:copyright", NS)
                self.assertEqual(derechos.attrib["author"], "Colaboradores de OpenStreetMap")
                self.assertEqual(derechos.findtext("g:license", namespaces=NS), mapa.URL_LICENCIA_ODBL)
                self.assertEqual(meta.find("g:link", NS).attrib["href"], mapa.URL_COPYRIGHT_OSM)
                self.assertIn("OpenStreetMap", track.findtext("g:cmt", namespaces=NS))
                self.assertIn("ODbL", track.findtext("g:cmt", namespaces=NS))
                trackpoints = track.findall("g:trkseg/g:trkpt", NS)
                self.assertEqual(
                    [(float(p.attrib["lat"]), float(p.attrib["lon"])) for p in trackpoints],
                    puntos,
                )
                self.assertEqual(len(gpxpy.parse(contenido.decode("utf-8")).tracks), 1)
                self.assertNotIn(b"<ele", contenido)
                self.assertNotIn(b"<time", contenido)

    def test_geojson_solo_agrega_cuatro_miembros_en_raiz(self):
        miembros = {"attribution", "license", "license_url", "copyright_url"}
        for fila in self.rutas:
            id_ruta = fila["id_ruta"]
            with self.subTest(ruta=id_ruta):
                original, _ = mapa.cargar_trazado(id_ruta)
                descargado = json.loads(mapa.geojson_descarga(id_ruta).decode("utf-8"))
                self.assertEqual(set(descargado) - set(original), miembros)
                for clave, valor in original.items():
                    self.assertEqual(descargado[clave], valor)
                self.assertEqual(descargado["attribution"], mapa.ATRIBUCION_OSM)
                self.assertEqual(descargado["license"], mapa.LICENCIA_ODBL)
                self.assertEqual(descargado["license_url"], mapa.URL_LICENCIA_ODBL)
                self.assertEqual(descargado["copyright_url"], mapa.URL_COPYRIGHT_OSM)

    def test_utf8_con_tilde_en_nombre_real(self):
        id_ruta = "R003"  # Sendero Cascada Cóndor Machay
        fila = next(fila for fila in self.rutas if fila["id_ruta"] == id_ruta)
        self.assertIn("Cóndor", fila["nombre_ruta"])
        _, puntos = mapa.cargar_trazado(id_ruta)
        gpx = mapa.gpx_desde_puntos(id_ruta, fila["nombre_ruta"], puntos)
        geojson = mapa.geojson_descarga(id_ruta)
        self.assertIn("Cóndor", ET.fromstring(gpx).findtext("g:metadata/g:name", namespaces=NS))
        self.assertIn("Cóndor", json.loads(geojson.decode("utf-8"))["features"][0]["properties"]["destino"])

    def test_identificador_invalido_no_puede_salir_de_trazados(self):
        with self.assertRaises(ValueError):
            mapa.ruta_trazado("../inventario")
        with self.assertRaises(ValueError):
            mapa.geojson_descarga("../inventario")


if __name__ == "__main__":
    unittest.main()
