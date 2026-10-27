"""Pruebas de la clasificación relativa de esfuerzo con K-means."""

import importlib.util
import os
from pathlib import Path
import sys
import unittest

if sys.platform == "win32":
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"
    os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("modelo_fisico", RAIZ / "06_scripts/evaluar_kmeans_esfuerzo.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ModeloFisicoTests(unittest.TestCase):
    def test_ari_y_silueta_con_particiones_conocidas(self):
        self.assertAlmostEqual(m.ari([0, 0, 1, 1], [1, 1, 0, 0]), 1.0)
        self.assertAlmostEqual(m.ari([0, 0, 1, 1], [0, 1, 0, 1]), -0.5)
        x = np.array([[0., 0.], [1., 1.], [5., 5.], [6., 6.]])
        self.assertGreater(m.silueta(x, np.array([0, 0, 1, 1])), 0.7)

    def test_modelo_actual_y_parametros_reproducen_las_20(self):
        datos = m.cargar()
        resumen, escenarios, asignaciones = m.evaluar(datos, "2026-10-22")
        self.assertEqual(len(datos), 20)
        self.assertEqual(set(resumen.k), {2, 3, 4})
        k2 = resumen.set_index("k").loc[2]
        self.assertEqual(k2.tamanos, "8/12")
        self.assertEqual(k2.ari_semillas_min, 1)
        self.assertEqual(k2.ari_ward, 1)
        self.assertGreater(k2.silueta, 0.5)
        k3 = resumen.set_index("k").loc[3]
        self.assertEqual(k3.tamanos, "2/6/12")
        self.assertEqual(k3.ari_semillas_min, 1)
        self.assertLess(k3.silueta, k2.silueta)
        self.assertEqual(set(asignaciones.grupo_relativo_k2), {0, 1})
        self.assertEqual(sum(asignaciones.sensible_a_parametros.eq("si")), 4)
        self.assertEqual(set(asignaciones.loc[asignaciones.sensible_a_parametros.eq("si"), "id_ruta"]),
                         {"R017", "R019", "R020", "R021"})
        self.assertEqual(escenarios.set_index("escenario").loc["ascenso_crudo", "ari_con_base"], 1)
        parametros = m.parametros_modelo(datos, asignaciones, "2026-10-22")
        for fila in asignaciones.itertuples():
            predicha = m.asignar_nueva_ruta(fila.distancia_total_km, fila.ascenso_total_m, parametros)
            self.assertEqual(predicha, fila.grupo_relativo_k2)
        dbs = m.contraste_dbscan(datos, asignaciones).set_index(["eps", "min_samples"])
        caso = dbs.loc[(0.5, 3)]
        self.assertEqual((caso.grupos_dbscan, caso.n_ruido, caso.n_comparables), (2, 4, 16))
        self.assertEqual(caso.ari_con_kmeans_solo_no_ruido, 1)
        self.assertEqual(set(caso.rutas_ruido.split("|")), {"R001", "R003", "R006", "R022"})

    def test_altitud_y_pendiente_no_entran_al_modelo(self):
        self.assertEqual(m.VARIABLES, ("distancia_total_km", "ascenso_total_m"))
        datos = m.cargar()
        base = m.ajustar(datos, 2)["etiquetas"]
        modificado = datos.copy()
        modificado["elevacion_max_m"] *= 10
        modificado["pendiente_media_abs_pct"] *= 10
        self.assertTrue(np.array_equal(base, m.ajustar(modificado, 2)["etiquetas"]))
        with self.assertRaises(ValueError):
            m.asignar_nueva_ruta(-1, 200, m.parametros_modelo(datos, m.evaluar(datos, "2026-10-22")[2], "2026-10-22"))


if __name__ == "__main__":
    unittest.main()
