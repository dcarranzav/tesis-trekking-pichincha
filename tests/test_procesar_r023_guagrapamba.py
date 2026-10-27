"""La R023 debe proceder del XML íntegro archivado y acabar en la cascada."""

from hashlib import sha256
import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "06_scripts/procesar_r023_guagrapamba.py"
SPEC = importlib.util.spec_from_file_location("procesar_r023_guagrapamba", SCRIPT)
MODULO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULO)


class ValidacionGuagrapamba(unittest.TestCase):
    def test_fuente_y_extremos(self):
        self.assertEqual(sha256(MODULO.FUENTE.read_bytes()).hexdigest().upper(), MODULO.SHA_FUENTE)
        linea, datos = MODULO.construir()
        self.assertEqual(len(datos["refs"]), 26)
        self.assertEqual(datos["refs"][-1], MODULO.ID_CASCADA)
        self.assertEqual(len(linea.coords), 26)
        self.assertTrue(linea.is_simple)
        self.assertLess(datos["distancia_inicio_parqueadero_m"], 30)


if __name__ == "__main__":
    unittest.main()
