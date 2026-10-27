"""Comparación personalizada sin convertir límites en dificultad o seguridad."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "06_scripts"))
import vista_rutas as vr


class CoincidenciasLimites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalogo, destinos = vr.cargar_catalogo(), vr.cargar_destinos()
        cls.yellow = vr.alternativas_de_destino(catalogo, "Mindo", "Yellow House", destinos)
        cls.mirador = vr.alternativas_de_destino(catalogo, "Mindo", "Mirador (Mindo Hermit Trail)", destinos)

    def test_filtra_sin_ocultar_alternativas(self):
        resultado = vr.coincidencias_limites(self.yellow, distancia_max_km=5.6, ascenso_max_m=300)
        self.assertEqual([r["id_ruta"] for r in resultado], ["R017", "R021", "R020"])
        self.assertTrue(resultado[0]["coincide"])
        self.assertFalse(resultado[1]["coincide"])
        self.assertIn("supera la distancia indicada", resultado[1]["razones"])
        self.assertEqual(len(resultado), 3)

    def test_sin_limites_no_es_recomendacion(self):
        resultado = vr.coincidencias_limites(self.yellow)
        self.assertTrue(all(r["coincide"] for r in resultado))
        self.assertTrue(all("nivel" not in r and "recomendacion" not in r for r in resultado))

    def test_destinos_diferentes_se_rechazan(self):
        with self.assertRaises(ValueError):
            vr.coincidencias_limites(self.yellow + self.mirador)

    def test_limite_invalido(self):
        with self.assertRaises(ValueError):
            vr.coincidencias_limites(self.yellow, distancia_max_km=0)
        with self.assertRaises(ValueError):
            vr.coincidencias_limites(self.yellow, ascenso_max_m="mucho")


if __name__ == "__main__":
    unittest.main()
