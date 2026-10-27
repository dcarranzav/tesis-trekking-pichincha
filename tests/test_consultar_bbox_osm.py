"""Controles sin conexión de la inspección de vías OSM candidatas."""

import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ARCHIVO = Path(__file__).resolve().parents[1] / "06_scripts/consultar_bbox_osm.py"
especificacion = importlib.util.spec_from_file_location("consultar_bbox_osm", ARCHIVO)
modulo = importlib.util.module_from_spec(especificacion)
assert especificacion.loader is not None
especificacion.loader.exec_module(modulo)


class ConsultarBBoxOSMTests(unittest.TestCase):
    def test_filtra_nombres_y_tipo_peatonal(self):
        raiz = ET.fromstring("""
        <osm>
          <way id="3"><nd ref="1"/><tag k="highway" v="path"/></way>
          <way id="2"><nd ref="1"/><tag k="highway" v="road"/><tag k="name" v="Carretera"/></way>
          <way id="1"><nd ref="1"/><nd ref="2"/><tag k="highway" v="footway"/><tag k="name" v="Sendero A"/></way>
        </osm>
        """)
        filas = modulo.inspeccionar(raiz)
        self.assertEqual([fila["id"] for fila in filas], ["1"])
        self.assertEqual(filas[0]["nodos"], 2)
        self.assertEqual(len(modulo.inspeccionar(raiz, True)), 2)

    def test_rechaza_bbox_invertida_o_extensa(self):
        for bbox in [(-78.5, -0.5, -78.6, -0.4), (-79, -1, -78, 0)]:
            with self.subTest(bbox=bbox):
                with self.assertRaises(ValueError):
                    modulo.validar_bbox(bbox)

    def test_admite_zonas_predefinidas(self):
        for bbox in modulo.ZONAS.values():
            modulo.validar_bbox(bbox)


if __name__ == "__main__":
    unittest.main()
