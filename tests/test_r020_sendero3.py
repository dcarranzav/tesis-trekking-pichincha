"""Comprueba la topología de la variante sin consultar la red ni reescribir datos."""

import importlib.util
from pathlib import Path
import unittest


ARCHIVO = Path(__file__).resolve().parents[1] / "06_scripts/procesar_r020_sendero3.py"
especificacion = importlib.util.spec_from_file_location("procesar_r020_sendero3", ARCHIVO)
modulo = importlib.util.module_from_spec(especificacion)
assert especificacion.loader is not None
especificacion.loader.exec_module(modulo)


class VarianteSendero3Tests(unittest.TestCase):
    def test_desvio_continuo_y_diferenciado(self):
        principal = modulo.leer_via(modulo.ORIGINAL_PRINCIPAL, "299595681", "Yellow House Trail")
        desvio = modulo.leer_via(modulo.ORIGINAL_DESVIO, "299595680", "Sendero 3")
        linea = modulo.combinar(principal, desvio)
        self.assertTrue(linea.is_valid and linea.is_simple)
        self.assertEqual(len(linea.coords), 66)
        self.assertEqual(linea.coords[0], principal[1][0])
        self.assertEqual(linea.coords[-1], principal[1][-1])

    def test_rechaza_desvio_sin_dos_contactos(self):
        principal = (["1", "2", "3"], [(0, 0), (1, 0), (2, 0)])
        desvio = (["2", "4"], [(1, 0), (1, 1)])
        with self.assertRaises(AssertionError):
            modulo.combinar(principal, desvio)


if __name__ == "__main__":
    unittest.main()
