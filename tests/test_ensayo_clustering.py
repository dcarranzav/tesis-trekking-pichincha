"""Pruebas de los límites del análisis exploratorio."""

import importlib.util
import os
from pathlib import Path
import unittest

# Debe fijarse antes de cargar NumPy/MKL en el proceso de pruebas Windows.
os.environ["MKL_THREADING_LAYER"] = "SEQUENTIAL"

import numpy as np
import pandas as pd


ARCHIVO = Path(__file__).resolve().parents[1] / "06_scripts/explorar_modelo_clasificacion.py"
especificacion = importlib.util.spec_from_file_location("explorar_modelo", ARCHIVO)
modulo = importlib.util.module_from_spec(especificacion)
assert especificacion.loader is not None
especificacion.loader.exec_module(modulo)


class EnsayoClusteringTests(unittest.TestCase):
    def test_usa_solo_rutas_elegibles(self):
        datos = modulo.cargar_elegibles()
        self.assertGreater(len(datos), 0)
        self.assertNotIn("R002", set(datos["id_ruta"]))
        self.assertNotIn("R005", set(datos["id_ruta"]))
        self.assertNotIn("R012", set(datos["id_ruta"]))
        self.assertNotIn("R014", set(datos["id_ruta"]))

    def test_silueta_con_dos_grupos_separados(self):
        puntos = np.array([[0.0], [0.1], [10.0], [10.1]])
        etiquetas = np.array([0, 0, 1, 1])
        self.assertGreater(modulo.silueta_euclidea(puntos, etiquetas), 0.98)

    def test_rechaza_grupo_unitario(self):
        puntos = np.array([[0.0], [0.1], [10.0]])
        etiquetas = np.array([0, 0, 1])
        with self.assertRaisesRegex(ValueError, "unitarios"):
            modulo.silueta_euclidea(puntos, etiquetas)

    def test_motor_sklearn_con_grupos_no_unitarios(self):
        datos = pd.DataFrame({
            "id_ruta": [f"T{i}" for i in range(6)],
            "id_destino": ["D1"] * 6,
            "distancia_total_km": [1.0, 1.1, 1.2, 8.0, 8.1, 8.2],
            "ascenso_total_m": [50, 55, 60, 500, 510, 520],
        })
        resultados, asignaciones = modulo.evaluar(
            "prueba", datos, ["distancia_total_km", "ascenso_total_m"], motor="sklearn"
        )
        dos_grupos = next(fila for fila in resultados if fila["k"] == 2)
        self.assertEqual(dos_grupos["tamano_minimo"], 3)
        self.assertEqual(len([fila for fila in asignaciones if fila["k"] == 2]), 6)

    def test_sensibilidad_retira_destinos_representados_y_r006(self):
        datos = modulo.cargar_elegibles()
        escenarios = {
            nombre: tabla
            for nombre, tabla, _ in modulo.construir_escenarios(datos, "sklearn")
        }
        self.assertIn("sin_destino_d010", escenarios)
        self.assertEqual(
            len(escenarios["sin_destino_d010"]),
            len(datos) - int(datos["id_destino"].eq("D010").sum()),
        )
        self.assertFalse(escenarios["sin_destino_d010"]["id_destino"].eq("D010").any())
        self.assertNotIn("R006", set(escenarios["sin_r006_atipico_eda"]["id_ruta"]))
        self.assertNotIn("R021", set(escenarios["sin_r021_senderos_1_2"]["id_ruta"]))
        self.assertNotIn("R022", set(escenarios["sin_r022_ilalo_pendiente"]["id_ruta"]))
        self.assertEqual(len(escenarios["sin_r022_ilalo_pendiente"]), len(datos) - 1)
        self.assertNotIn("R026", set(escenarios["sin_r026_guarumos_solapamiento_dem"]["id_ruta"]))
        self.assertEqual(len(escenarios["sin_r026_guarumos_solapamiento_dem"]), len(datos) - 1)
        self.assertNotIn("R027", set(escenarios["sin_r027_sendero_corto"]["id_ruta"]))
        self.assertEqual(len(escenarios["sin_r027_sendero_corto"]), len(datos) - 1)
        self.assertEqual(len(escenarios["base_4_variables"]), len(datos))

    def test_sensibilidad_separa_distancia_y_ascenso(self):
        datos = modulo.cargar_elegibles()
        escenarios = {
            nombre: (tabla, variables)
            for nombre, tabla, variables in modulo.construir_escenarios(datos, "sklearn")
        }
        for nombre, ausente in (
            ("sin_variable_distancia", "distancia_total_km"),
            ("sin_variable_ascenso", "ascenso_total_m"),
        ):
            tabla, variables = escenarios[nombre]
            self.assertEqual(len(tabla), len(datos))
            self.assertEqual(len(variables), 3)
            self.assertNotIn(ausente, variables)


if __name__ == "__main__":
    unittest.main()
