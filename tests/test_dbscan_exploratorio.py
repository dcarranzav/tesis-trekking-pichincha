"""El contraste DBSCAN no convierte ruido ni grupos en clases finales."""

import importlib.util
import os
from pathlib import Path
import unittest

os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"

import numpy as np
import pandas as pd


RUTA = Path(__file__).resolve().parents[1] / "06_scripts/ensayar_dbscan_exploratorio.py"
spec = importlib.util.spec_from_file_location("ensayar_dbscan_exploratorio", RUTA)
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


class DBSCANExploratorioTests(unittest.TestCase):
    def test_solo_elegibles(self):
        datos = modulo.cargar_datos()
        self.assertTrue(datos["estado_modelado"].eq("elegible_actual").all())
        self.assertNotIn("R002", set(datos["id_ruta"]))

    def test_sensibilidad_y_ruido_separados(self):
        datos = pd.DataFrame({
            "id_ruta": ["A", "B", "C", "D", "E"],
            "distancia_total_km": [1, 1.1, 5, 5.1, 20],
            "ascenso_total_m": [10, 11, 50, 51, 200],
            "elevacion_max_m": [100, 101, 500, 501, 2000],
            "pendiente_media_abs_pct": [2, 2.1, 5, 5.1, 20],
        })
        metricas, asignaciones = modulo.evaluar(datos, epsilon=(0.2,), min_samples=(2,))
        self.assertEqual(metricas.iloc[0]["n_grupos"], 2)
        self.assertEqual(metricas.iloc[0]["n_ruido"], 1)
        self.assertEqual(len(asignaciones), 5)
        self.assertEqual(asignaciones.loc[asignaciones.id_ruta.eq("E"), "grupo_numerico_sin_orden"].iloc[0], -1)

    def test_silueta_indefinida_con_un_grupo(self):
        datos = modulo.cargar_datos()
        metricas, _ = modulo.evaluar(datos, epsilon=(100,), min_samples=(2,))
        self.assertEqual(metricas.iloc[0]["n_grupos"], 1)
        self.assertTrue(np.isnan(metricas.iloc[0]["silueta_sin_ruido"]))


if __name__ == "__main__":
    unittest.main()
