"""Pruebas del experimento K-means k=3 (contraste exploratorio de dificultad física estimada)."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

if sys.platform == "win32":
    os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"
    os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]


def _cargar_modulo(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "06_scripts" / archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


k3 = _cargar_modulo("kmeans_k3", "evaluar_kmeans_k3_dificultad.py")
previo = _cargar_modulo("kmeans_previo", "evaluar_kmeans_esfuerzo.py")
FECHA = "2026-11-10"


class ExperimentoK3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.salida = Path(cls.tmp.name)
        cls.res = k3.ejecutar(FECHA, cls.salida)
        cls.asig = cls.res["salidas"]["asignaciones"].set_index("id_ruta")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_integridad_de_ids_y_ausencia_de_faltantes(self):
        dataset = pd.read_csv(k3.TABLAS / "dataset_clasificacion_rutas.csv")
        regla = pd.read_csv(k3.TABLAS / "clasificacion_dificultad_fisica_2026-10-23.csv")
        self.assertEqual(len(dataset), 27)
        self.assertEqual(int(dataset.estado_modelado.eq("elegible_actual").sum()), 20)
        self.assertEqual(set(self.asig.index), set(regla.id_ruta))
        self.assertTrue(self.asig.index.is_unique)
        self.assertEqual(len(self.asig), 20)
        self.assertFalse(self.asig[["distancia_total_km", "ascenso_total_m", "esfuerzo_estimado_h",
                                    "silueta_individual_k3", "margen_relativo_k3"]].isna().any().any())
        self.assertEqual(self.res["parametros"]["ids_entrenamiento"], sorted(regla.id_ruta))

    def test_reproduce_las_metricas_del_modelo_previo(self):
        m = self.res["salidas"]["metricas"].set_index("k")
        self.assertEqual(m.loc[2, "tamanos"], "12/8")
        self.assertAlmostEqual(m.loc[2, "silueta"], 0.5919, places=4)
        self.assertEqual(m.loc[3, "tamanos"], "12/6/2")
        self.assertAlmostEqual(m.loc[3, "silueta"], 0.5895, places=4)
        self.assertAlmostEqual(m.loc[3, "ari_ward"], 0.9246, places=4)
        self.assertEqual(m.loc[3, "ari_semillas_min"], 1.0)
        # silueta propia del proyecto coincide con la de scikit-learn
        datos = k3.cargar()
        a3 = k3.ajustar(datos, 3)
        self.assertAlmostEqual(previo.silueta(a3["x"], a3["etiquetas"]), a3["silueta"], places=8)

    def test_grupos_ordenados_y_reproducibles_con_centroides(self):
        p = self.res["parametros"]
        for ruta, fila in self.asig.iterrows():
            r = k3.asignar_nueva_ruta(fila.distancia_total_km, fila.ascenso_total_m, p)
            self.assertEqual(r["grupo_indice"], fila.grupo_k3 + 1, ruta)
            self.assertFalse(r["extrapolacion"])
        sumas = np.asarray(p["centroides_estandarizados_k3"]).sum(axis=1)
        self.assertTrue(np.all(np.diff(sumas) > 0))
        self.assertEqual(sorted(self.asig.index[self.asig.grupo_k3 == 2]), ["R001", "R006"])
        self.assertTrue(k3.asignar_nueva_ruta(30.0, 3000.0, p)["extrapolacion"])

    def test_misma_ejecucion_produce_las_mismas_asignaciones(self):
        with tempfile.TemporaryDirectory() as otro:
            segunda = k3.ejecutar(FECHA, Path(otro))
        self.assertEqual(segunda["salidas"]["asignaciones"].grupo_k3.tolist(), self.asig.reset_index().grupo_k3.tolist())

    def test_no_sobrescribe_resultados_existentes(self):
        nombres = {p.name for p in self.salida.iterdir()}
        self.assertTrue(all(n.startswith("kmeans_k3_") for n in nombres), nombres)
        self.assertIn(f"kmeans_k3_parametros_{FECHA}.json", nombres)
        json.loads((self.salida / f"kmeans_k3_parametros_{FECHA}.json").read_text(encoding="utf-8"))

    def test_dbscan_separa_cobertura_y_acuerdo(self):
        d = self.res["salidas"]["dbscan"]
        caso = d[(d.eps == 0.5) & (d.min_samples == 3)].iloc[0]
        self.assertEqual((caso.grupos_dbscan, caso.n_ruido), (2, 4))
        self.assertAlmostEqual(caso.cobertura, 0.8)
        self.assertEqual(caso.ari_k3_solo_no_ruido, 1.0)
        self.assertLess(caso.ari_k3_ruido_como_grupo_20, 1.0)
        uno = d[d.grupos_dbscan == 1].iloc[0]
        self.assertTrue(pd.isna(uno.ari_k3_solo_no_ruido) or uno.ari_k3_solo_no_ruido == "")

    def test_sensibilidad_registra_todos_los_escenarios_sin_fallos(self):
        s = self.res["salidas"]["sensibilidad"]
        self.assertEqual(int(s.fallo.fillna("").ne("").sum()), 0)
        self.assertEqual(int(s.familia.eq("retirar_una").sum()), 20)
        self.assertIn("sin_R026_R027", set(s.escenario))
        self.assertEqual(s.set_index("escenario").loc["ascenso_crudo", "ari_con_base"] < 0.8, True)

    def test_logica_de_decision_a_priori(self):
        metricas = pd.DataFrame({"k": [2, 3], "silueta": [0.6, 0.6], "ari_semillas_min": [1.0, 1.0]})
        sens = pd.DataFrame({"escenario": ["p", "ascenso_mediana5", "ascenso_crudo", "sin_a", "u"],
                             "familia": ["pesos_moderados", "filtrado_dem", "filtrado_dem", "retirar_una", "una_por_destino"],
                             "fallo": [""] * 5, "ari_con_base": [1.0] * 5})
        solap = pd.DataFrame({"medida": ["esfuerzo_h"], "se_solapan": ["no"]})
        inv = pd.DataFrame(columns=["adyacentes"])
        self.assertEqual(k3.evaluar_criterios(metricas, sens, solap, inv, [5, 5, 5])[1], "A")
        self.assertEqual(k3.evaluar_criterios(metricas, sens, solap, inv, [12, 6, 2])[1], "C")
        self.assertEqual(k3.evaluar_criterios(metricas, sens, pd.DataFrame({"medida": ["esfuerzo_h"], "se_solapan": ["si"]}),
                                              inv, [5, 5, 5])[1], "B")
        sens2 = sens.copy()
        sens2.loc[2, "ari_con_base"] = 0.5
        self.assertEqual(k3.evaluar_criterios(metricas, sens2, solap, inv, [12, 6, 2])[1], "B")

    def test_ordenar_grupos_usa_solo_las_variables_del_modelo(self):
        x = np.array([[5., 5.], [5., 6.], [0., 0.], [0., 1.], [2., 2.], [2., 3.]])
        et = k3.ordenar_grupos(np.array([2, 2, 0, 0, 1, 1]), x)
        self.assertEqual(et.tolist(), [2, 2, 0, 0, 1, 1])


if __name__ == "__main__":
    unittest.main()
