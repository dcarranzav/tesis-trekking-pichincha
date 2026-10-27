import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "06_scripts"))
import inspeccionar_zona_osm as i  # noqa: E402


class Inspeccion(unittest.TestCase):
    def test_consulta_es_local_y_pequena(self):
        q = i.consulta(-0.21, -78.28, 1500)
        self.assertIn("around:1500,-0.21,-78.28", q)
        self.assertNotIn("-79.2", q)

    def test_resumen_muestra_extremos_y_sac(self):
        datos = {"elements": [{"type": "way", "id": 1, "nodes": [7, 8, 9], "geometry": [],
                               "tags": {"highway": "path", "sac_scale": "hiking", "name": "S"}},
                              {"type": "node", "id": 2, "tags": {"name": "Cima", "natural": "peak"}}]}
        r = i.resumen(datos)
        self.assertIn("sac=hiking", r[0])
        self.assertIn("ini=7 fin=9", r[0])
        self.assertIn("Cima", r[1])

    def test_resumen_xml(self):
        xml = (b'<osm><node id="1" lat="0" lon="0"/><node id="2" lat="0" lon="0"><tag k="name" v="Cima"/><tag k="natural" v="peak"/></node>'
               b'<way id="9"><nd ref="1"/><nd ref="2"/><tag k="highway" v="path"/><tag k="sac_scale" v="hiking"/></way>'
               b'<way id="10"><nd ref="1"/><nd ref="2"/><tag k="building" v="yes"/></way></osm>')
        r = i.resumen_xml(xml)
        self.assertEqual(len(r), 2)
        self.assertIn("sac=hiking", r[0])
        self.assertIn("ini=1 fin=2", r[0])


if __name__ == "__main__":
    unittest.main()
