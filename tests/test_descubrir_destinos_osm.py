"""Pruebas de la detección de candidatas (XML sintético; no usa la red)."""

import sys
import csv
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "06_scripts"))
import descubrir_destinos_osm as d  # noqa: E402

XML = """<osm><node id="1" lat="0" lon="0"/><node id="2" lat="0" lon="0.001"/>
<node id="3" lat="0" lon="0.002"><tag k="waterway" v="waterfall"/><tag k="name" v="Cascada X"/></node>
<node id="4" lat="0.01" lon="0"/>
<way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/><tag k="highway" v="path"/><tag k="name" v="S"/></way>
<way id="11"><nd ref="2"/><nd ref="3"/><tag k="highway" v="footway"/></way>
<way id="12"><nd ref="1"/><nd ref="4"/><tag k="highway" v="residential"/></way></osm>"""


class DescubrirDestinos(unittest.TestCase):
    def test_detecta_vias_que_terminan_en_destino_y_alternativas_al_mismo_nodo(self):
        filas = d.candidatas(ET.fromstring(XML), "t")
        self.assertEqual({f["id_via"] for f in filas}, {"10", "11"})
        f10 = next(f for f in filas if f["id_via"] == "10")
        self.assertEqual(f10["tipo_destino"], "waterway=waterfall")
        self.assertEqual(f10["otras_vias_mismo_destino"], "11")
        self.assertAlmostEqual(f10["longitud_m"], 222, delta=3)

    def test_ignora_calles_y_nodos_sin_destino(self):
        self.assertFalse([f for f in d.candidatas(ET.fromstring(XML), "t") if f["id_via"] == "12"])

    def test_overpass_detecta_extremo_en_destino(self):
        datos = {"osm3s": {"timestamp_osm_base": "2026-06-01T00:00:00Z"}, "elements": [
            {"type": "node", "id": 3, "lat": 0, "lon": 0.002, "tags": {"waterway": "waterfall", "name": "Cascada X"}},
            {"type": "way", "id": 10, "nodes": [1, 2, 3], "tags": {"highway": "path", "sac_scale": "hiking"},
             "geometry": [{"lat": 0, "lon": 0}, {"lat": 0, "lon": 0.001}, {"lat": 0, "lon": 0.002}]},
            {"type": "way", "id": 11, "nodes": [4, 5], "tags": {"highway": "path"},
             "geometry": [{"lat": 1, "lon": 1}, {"lat": 1, "lon": 1.001}]}]}
        filas = d.candidatas_overpass(datos, "t")
        self.assertEqual([(f["id_via"], f["nombre_destino"], f["fecha_datos_osm"][:4]) for f in filas], [("10", "Cascada X", "2026")])
        self.assertIn('node["waterway"="waterfall"]', d.consulta_overpass((-78.7, -0.2, -78.4, 0.1)))

    def test_teselas_cubren_la_caja(self):
        t = list(d.teselas(0, 0, 0.25, 0.1, 0.1))
        self.assertEqual(len(t), 3)
        self.assertEqual(t[-1][2], 0.25)

    def test_guardado_incremental_y_reanudacion_sin_duplicados(self):
        datos = {"elements": [
            {"type": "node", "id": 3, "lat": 0, "lon": 0.002,
             "tags": {"waterway": "waterfall", "name": "Cascada X"}},
            {"type": "way", "id": 10, "nodes": [1, 3], "tags": {"highway": "path"},
             "geometry": [{"lat": 0, "lon": 0}, {"lat": 0, "lon": 0.002}]},
        ]}
        cajas = [(0, 0, 0.1, 0.1), (0.1, 0, 0.2, 0.1)]
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "_tmp") as temporal:
            salida = Path(temporal) / "candidatas.csv"
            with patch.object(d, "descargar_overpass", return_value=datos) as consulta, patch.object(d.time, "sleep"):
                self.assertEqual(d.explorar_incremental(cajas, salida, "overpass", lambda _: None, 1), (1, 1))
                self.assertEqual(d.explorar_incremental(cajas, salida, "overpass", lambda _: None), (1, 0))
                self.assertEqual(consulta.call_count, 2)
            with salida.open(encoding="utf-8-sig", newline="") as archivo:
                self.assertEqual([fila["id_via"] for fila in csv.DictReader(archivo)], ["10"])
            with salida.with_name("candidatas.teselas.csv").open(encoding="utf-8-sig", newline="") as archivo:
                self.assertEqual(len(list(csv.DictReader(archivo))), 2)


if __name__ == "__main__":
    unittest.main()
