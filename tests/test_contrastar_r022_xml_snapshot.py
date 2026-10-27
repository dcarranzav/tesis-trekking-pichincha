"""La fuente exacta de R022 debe seguir reconciliando con sus derivados."""

import importlib.util
from pathlib import Path
import unittest


ARCHIVO = Path(__file__).resolve().parents[1] / "06_scripts/contrastar_r022_xml_snapshot.py"
ESPECIFICACION = importlib.util.spec_from_file_location("contrastar_r022_xml_snapshot", ARCHIVO)
MODULO = importlib.util.module_from_spec(ESPECIFICACION)
assert ESPECIFICACION.loader is not None
ESPECIFICACION.loader.exec_module(MODULO)


class ContrasteFuenteR022Tests(unittest.TestCase):
    def test_xml_snapshot_y_trazado_concuerdan(self):
        resultado = MODULO.contrastar()
        self.assertEqual(resultado["nodos"], 128)
        self.assertEqual(resultado["sha256"], MODULO.SHA_XML)
        self.assertEqual(resultado["vados_osm"], ["9996501327", "9996501328"])


if __name__ == "__main__":
    unittest.main()
