"""Verifica que R022 depende de la instantánea fijada y no de un enlace inventado."""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "06_scripts/procesar_r022_ilalo.py"
SPEC = importlib.util.spec_from_file_location("procesar_r022_ilalo", SCRIPT)
MODULO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULO)


class ValidacionProcesamientoIlalo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contenido = MODULO.FUENTE.read_bytes()
        cls.documento = json.loads(cls.contenido)

    def test_huella_y_geometria_completa(self):
        self.assertEqual(sha256(self.contenido).hexdigest().upper(), MODULO.HASH_FUENTE)
        linea, refs, distancia_poi = MODULO.construir(self.documento)
        self.assertEqual(len(refs), 128)
        self.assertEqual((refs[0], refs[-1]), (1369911783, 1323665115))
        self.assertEqual(len(linea.coords), 128)
        self.assertTrue(linea.is_simple)
        self.assertLess(distancia_poi, 10)

    def test_rechaza_via_incompleta(self):
        alterado = json.loads(self.contenido)
        alterado["way"]["geometry"].pop()
        with self.assertRaises(AssertionError):
            MODULO.construir(alterado)

    def test_rechaza_identidad_ajena(self):
        alterado = json.loads(self.contenido)
        alterado["way"]["id"] = 1
        with self.assertRaises(AssertionError):
            MODULO.construir(alterado)


if __name__ == "__main__":
    unittest.main()
