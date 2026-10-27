import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "06_scripts"))
import analizar_zona_osm as a  # noqa: E402

XML = """<osm>
<node id="1" lat="0" lon="0"/><node id="2" lat="0.0005" lon="0.0005"/><node id="3" lat="0.001" lon="0.001"/>
<node id="4" lat="0.001" lon="0"/><node id="5" lat="0" lon="-0.001"/>
<node id="9" lat="0.001" lon="0.001"><tag k="name" v="Mirador"/><tag k="tourism" v="viewpoint"/></node>
<way id="10"><nd ref="5"/><nd ref="1"/><tag k="highway" v="residential"/></way>
<way id="11"><nd ref="1"/><nd ref="2"/><nd ref="9"/><tag k="highway" v="path"/></way>
<way id="12"><nd ref="1"/><nd ref="4"/><nd ref="9"/><tag k="highway" v="footway"/></way>
<way id="13"><nd ref="5"/><nd ref="3"/><tag k="highway" v="path"/><tag k="access" v="no"/></way>
</osm>"""


class AnalisisZona(unittest.TestCase):
    def test_punto_de_interes_en_empalme_no_es_ruta(self):
        xml = """<osm>
<node id="1" lat="0" lon="0"><tag k="name" v="Mirador"/><tag k="tourism" v="viewpoint"/></node>
<node id="2" lat="0" lon="0.001"/><node id="3" lat="0" lon="-0.001"/>
<way id="10"><nd ref="3"/><nd ref="1"/><tag k="highway" v="residential"/></way>
<way id="11"><nd ref="1"/><nd ref="2"/><tag k="highway" v="path"/></way>
</osm>"""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "z.osm"
            p.write_text(xml, encoding="utf-8")
            self.assertEqual(a.candidatas(p), [])

    def test_camino_y_alternativa_por_nodos_compartidos(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "z.osm"
            p.write_text(XML, encoding="utf-8")
            filas = a.candidatas(p)
        self.assertEqual(len(filas), 1)
        f = filas[0]
        self.assertEqual((f["nombre"], f["inicio"]), ("Mirador", "1"))
        self.assertEqual(f["vias"], "11")
        self.assertEqual(f["alt_vias"], "12")  # la vía con access=no no se usa y no hay unión por cercanía


if __name__ == "__main__":
    unittest.main()
