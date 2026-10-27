"""El indicador de esfuerzo depende solo de distancia y ascenso, es continuo y no crea clases."""

import importlib.util
import os
from pathlib import Path
import unittest

os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("indicador", RAIZ / "06_scripts/calcular_indicador_esfuerzo.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class IndicadorEsfuerzoTests(unittest.TestCase):
    def test_formula_naismith(self):
        self.assertAlmostEqual(float(m.horas_equivalentes(10, 600)), 3.0)  # 10/5 + 600/600
        self.assertAlmostEqual(float(m.horas_equivalentes(5, 0)), 1.0)
        self.assertAlmostEqual(float(m.horas_equivalentes(0, 300)), 0.5)

    def test_monotonia_y_ausencia_de_altitud(self):
        base = m.horas_equivalentes(4.0, 300.0)
        self.assertGreater(m.horas_equivalentes(4.5, 300.0), base)
        self.assertGreater(m.horas_equivalentes(4.0, 350.0), base)
        # la firma de la función no admite altitud: la altitud no puede influir
        self.assertEqual(m.horas_equivalentes.__code__.co_varnames[:4], ("distancia_km", "ascenso_m", "v", "r"))

    def test_rangos_uno_es_mayor_y_empates(self):
        self.assertEqual(list(m.rangos([1.0, 3.0, 2.0])), [3.0, 1.0, 2.0])
        self.assertEqual(list(m.rangos([2.0, 2.0, 1.0])), [1.5, 1.5, 3.0])

    def test_ascenso_ida_y_vuelta_suma_subida_y_bajada(self):
        z = np.array([0.0, 10.0, 5.0, 15.0])
        self.assertAlmostEqual(m.ascenso_total(z, "ida_y_vuelta"), 25.0)  # 20 de subida + 5 de bajada
        self.assertAlmostEqual(m.ascenso_total(z, "circular"), 20.0)

    def test_tobler_mas_lento_en_pendiente_fuerte(self):
        d = np.array([0.0, 100.0, 200.0])
        llano = m.tobler_horas(d, np.array([0.0, 0.0, 0.0]), "circular")
        fuerte = m.tobler_horas(d, np.array([0.0, 30.0, 60.0]), "circular")
        self.assertGreater(fuerte, llano)

    def test_datos_reales_reproducen_ascenso_y_no_crean_clases(self):
        e = m.cargar()
        p, _ = m.perfiles(e)  # falla si el ascenso del dataset no se reproduce
        t = m.tabla_indicador(e, p)
        self.assertEqual(len(t), 20)
        self.assertTrue(t["id_ruta"].is_unique)
        self.assertNotIn("clase", " ".join(t.columns).lower())
        self.assertIn("altitud_maxima_advertencia_m", t.columns)
        np.testing.assert_allclose(t["hen_horas_equivalentes"], e["distancia_total_km"] / 5 + e["ascenso_total_m"] / 600)
        for prohibido in ("niveles_esfuerzo_finales", "validacion_modelo_final"):
            self.assertFalse(list((RAIZ / "07_resultados/tablas").glob(f"{prohibido}*")))


if __name__ == "__main__":
    unittest.main()
