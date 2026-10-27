"""Comprueba la procedencia y los extremos de R027."""

import importlib.util
from pathlib import Path
import unittest


ARCHIVO = Path(__file__).resolve().parents[1] / "06_scripts/procesar_r027_sendero_viento.py"
SPEC = importlib.util.spec_from_file_location("procesar_sendero_viento", ARCHIVO)
MODULO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULO)


class SenderoVientoTests(unittest.TestCase):
    def test_extremos_y_continuidad_sin_conector(self):
        coords, datos = MODULO.construir()
        self.assertEqual(datos["refs"][0], MODULO.NODO_INICIO)
        self.assertEqual(datos["refs"][-1], MODULO.NODO_FIN)
        self.assertEqual(len(coords), len(datos["refs"]))
        self.assertEqual(len(datos["refs"]), len(set(datos["refs"])))
        self.assertGreater(datos["distancia_ida_km"], 0.7)
        self.assertLess(datos["distancia_ida_km"], 0.76)
        self.assertLess(datos["separacion_mirador_m"], 5)


if __name__ == "__main__":
    unittest.main()
