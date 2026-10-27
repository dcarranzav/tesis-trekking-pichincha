"""Pruebas de la clasificación física estimada Fácil/Moderada/Difícil."""

import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np


RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "clasificacion_tres_niveles", RAIZ / "06_scripts" / "clasificar_dificultad_fisica.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
sys.path.insert(0, str(RAIZ / "06_scripts"))
import vista_rutas as vr


class ClasificacionDificultadFisicaTests(unittest.TestCase):
    def test_formula_mide_adaptada(self):
        horizontal, desnivel, total = m.horas_marcha_efectiva(4.0, 400.0, 0.0)
        self.assertAlmostEqual(horizontal, 1.0)
        self.assertAlmostEqual(desnivel, 1.0)
        self.assertAlmostEqual(total, 1.5)

    def test_umbrales_inclusivos(self):
        self.assertEqual(m.nivel_por_horas(1.0), (1, "Fácil"))
        self.assertEqual(m.nivel_por_horas(1.0001), (2, "Moderada"))
        self.assertEqual(m.nivel_por_horas(3.0), (2, "Moderada"))
        self.assertEqual(m.nivel_por_horas(3.0001), (3, "Difícil"))

    def test_ida_y_vuelta_incluye_el_regreso(self):
        subida, bajada = m.desniveles_recorrido(np.array([100.0, 150.0, 120.0]), "ida_y_vuelta")
        self.assertAlmostEqual(subida, 80.0)
        self.assertAlmostEqual(bajada, 80.0)

    def test_circular_conserva_desniveles_del_perfil(self):
        subida, bajada = m.desniveles_recorrido(np.array([100.0, 150.0, 120.0, 100.0]), "circular")
        self.assertAlmostEqual(subida, 50.0)
        self.assertAlmostEqual(bajada, 50.0)

    def test_muestra_real_cubre_tres_niveles(self):
        datos = m.cargar_muestra()
        tabla = m.clasificar(datos)
        self.assertEqual(len(tabla), 20)
        self.assertTrue(tabla["id_ruta"].is_unique)
        self.assertEqual(
            tabla["dificultad_fisica_estimada"].value_counts().to_dict(),
            {"Moderada": 10, "Fácil": 8, "Difícil": 2},
        )
        niveles = tabla.set_index("id_ruta")["dificultad_fisica_estimada"]
        self.assertEqual(niveles["R001"], "Difícil")
        self.assertEqual(niveles["R018"], "Fácil")

    def test_sensibilidad_no_cambia_la_cobertura(self):
        datos = m.cargar_muestra()
        base = m.clasificar(datos)
        detalle, resumen = m.sensibilidad(datos, base)
        self.assertEqual(len(detalle), 5 * 20)
        self.assertEqual(set(resumen["id_ruta"]), set(base["id_ruta"]))
        self.assertTrue(set(resumen["sensible_a_supuestos"]).issubset({"si", "no"}))

    def test_capa_de_interfaz_lee_la_clasificacion_sin_habilitar_recomendacion(self):
        catalogo = vr.cargar_catalogo()
        dificil = vr.dificultad_fisica_estimada("R001", catalogo)
        facil = vr.dificultad_fisica_estimada("R018", catalogo)
        self.assertEqual(dificil["nivel"], "Difícil")
        self.assertEqual(facil["nivel"], "Fácil")
        self.assertFalse(vr.estado_clasificacion(catalogo)["disponible"])


if __name__ == "__main__":
    unittest.main()
