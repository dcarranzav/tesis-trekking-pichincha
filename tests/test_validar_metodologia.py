"""La validación metodológica es reproducible y no habilita clases ni recomendaciones."""

import importlib.util
import os
from pathlib import Path
import unittest

os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validar", RAIZ / "06_scripts/validar_metodologia_clasificacion.py")
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)


def sintetico():
    rng = np.random.default_rng(1)
    bajo = rng.normal([2, 100, 1500, 10], [0.3, 15, 50, 1], size=(12, 4))
    alto = rng.normal([9, 800, 3000, 25], [0.3, 15, 50, 1], size=(5, 4))
    datos = pd.DataFrame(np.vstack([bajo, alto]), columns=modulo.VARIABLES)
    datos["pendiente_p95_abs_pct"] = datos["pendiente_media_abs_pct"] * 3
    datos["id_ruta"] = [f"S{i:02d}" for i in range(len(datos))]
    datos["id_destino"] = [f"D{i:02d}" for i in range(len(datos))]
    return datos


class ValidacionMetodologicaTests(unittest.TestCase):
    def test_datos_reales_integros(self):
        datos = modulo.cargar()
        self.assertTrue(datos["id_ruta"].is_unique)
        self.assertTrue(datos["estado_modelado"].eq("elegible_actual").all())
        self.assertNotIn("R002", set(datos["id_ruta"]))
        z = modulo.escalar(datos, modulo.VARIABLES)
        self.assertTrue(np.allclose(z.mean(axis=0), 0, atol=1e-9))
        self.assertTrue(np.allclose(z.std(axis=0), 1, atol=1e-9))

    def test_recupera_dos_grupos_separados_y_es_estable(self):
        datos = sintetico()
        _, mejor, ajustes, lab = modulo.particion(datos, modulo.VARIABLES, 2)
        self.assertEqual(sorted(np.bincount(lab)), [5, 12])
        self.assertEqual(set(datos.id_ruta[lab == 1]), set(datos.id_ruta[12:]))
        from sklearn.metrics import adjusted_rand_score
        self.assertGreater(min(adjusted_rand_score(mejor.labels_, a.labels_) for a in ajustes), 0.99)

    def test_reetiquetado_ordena_por_ascenso(self):
        lab = modulo.reetiquetar(np.array([1, 1, 0, 0]), np.array([800.0, 700.0, 10.0, 20.0]))
        self.assertEqual(list(lab), [1, 1, 0, 0])

    def test_dbscan_marca_ruido_y_ari_no_definido_con_un_grupo(self):
        datos = sintetico()
        datos.loc[len(datos)] = [50, 3000, 4800, 60, 180, "S99", "D99"]
        metr, comp, _ = modulo.bloque_dbscan(datos)
        self.assertTrue((metr["n_ruido"] >= 0).all())
        un_grupo = comp[comp["n_grupos_dbscan"] < 2]
        self.assertTrue(un_grupo["ari_solo_no_ruido"].isna().all())

    def test_no_crea_archivos_de_habilitacion(self):
        fuente = (RAIZ / "06_scripts/validar_metodologia_clasificacion.py").read_text(encoding="utf-8")
        codigo = fuente.split('"""', 2)[2]  # sin el docstring, que los nombra para prohibirlos
        for prohibido in ("niveles_esfuerzo_finales", "validacion_modelo_final"):
            self.assertNotIn(prohibido, codigo.replace("validacion_modelo_final.json ni habilita", ""))
            self.assertFalse(list((RAIZ / "07_resultados/tablas").glob(f"{prohibido}*")))


if __name__ == "__main__":
    unittest.main()
