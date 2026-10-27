"""R024 y R025 deben proceder del XML íntegro archivado y terminar en el mismo mirador."""

from hashlib import sha256
import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "06_scripts/procesar_r024_r025_cerro_luz.py"
SPEC = importlib.util.spec_from_file_location("procesar_cerro_luz", SCRIPT)
MODULO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULO)


class ValidacionCerroLuz(unittest.TestCase):
    def test_fuente_extremos_y_variantes(self):
        self.assertEqual(sha256(MODULO.FUENTE.read_bytes()).hexdigest().upper(), MODULO.SHA_FUENTE)
        r = MODULO.construir()
        self.assertEqual(set(r), {"R024", "R025"})
        for _, datos in r.values():
            self.assertEqual(datos["refs"][0], MODULO.NODO_INICIO)
            self.assertEqual(datos["refs"][-1], MODULO.NODO_MIRADOR)
        self.assertLess(r["R024"][1]["distancia_ida_km"], 0.6)
        self.assertGreater(r["R025"][1]["distancia_ida_km"], 1.2)
        comunes = set(r["R024"][1]["refs"]) & set(r["R025"][1]["refs"])
        self.assertLess(len(comunes), 12)  # solo el inicio y el tramo final compartido


if __name__ == "__main__":
    unittest.main()
