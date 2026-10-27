"""Evita que la reejecución de notebooks de consulta altere productos GIS."""

import ast
from pathlib import Path
import unittest

import nbformat


RAIZ = Path(__file__).resolve().parents[1]
NOTEBOOKS = RAIZ / "05_notebooks"
PERMITIDOS = (
    "00_verificacion_entorno.ipynb",
    "01_validacion_documentacion.ipynb",
    "02_inspeccion_trazados_piloto.ipynb",
    "03_elevacion_piloto.ipynb",
    "04_ampliacion_rutas.ipynb",
)
TODOS = PERMITIDOS + ("05_validacion_metodologica.ipynb",)
METODOS_ESCRITURA = {
    "to_file", "to_csv", "to_json", "to_parquet", "mkdir",
    "write_text", "write_bytes", "writelines", "run_path",
}


class NotebooksDeLecturaTest(unittest.TestCase):
    def test_todos_los_notebooks_tienen_salidas_actualizadas(self):
        for nombre in TODOS:
            with self.subTest(notebook=nombre):
                notebook = nbformat.read(NOTEBOOKS / nombre, as_version=4)
                nbformat.validate(notebook)
                celdas = [c for c in notebook.cells if c.cell_type == "code"]
                self.assertTrue(celdas)
                self.assertEqual(
                    [c.execution_count for c in celdas],
                    list(range(1, len(celdas) + 1)),
                )
                for celda in celdas:
                    self.assertFalse(any(s.output_type == "error" for s in celda.outputs))

    def test_no_hay_llamadas_directas_de_escritura_en_celdas(self):
        for nombre in PERMITIDOS:
            notebook = nbformat.read(NOTEBOOKS / nombre, as_version=4)
            for numero, celda in enumerate(notebook.cells, start=1):
                if celda.cell_type != "code":
                    continue
                arbol = ast.parse(celda.source)
                for nodo in ast.walk(arbol):
                    if not isinstance(nodo, ast.Call):
                        continue
                    funcion = nodo.func
                    if isinstance(funcion, ast.Attribute):
                        with self.subTest(notebook=nombre, celda=numero):
                            self.assertNotIn(funcion.attr, METODOS_ESCRITURA)
                    if isinstance(funcion, ast.Name) and funcion.id == "open":
                        modo = nodo.args[1] if len(nodo.args) > 1 else next(
                            (kw.value for kw in nodo.keywords if kw.arg == "mode"), None
                        )
                        if isinstance(modo, ast.Constant) and isinstance(modo.value, str):
                            with self.subTest(notebook=nombre, celda=numero):
                                self.assertFalse(set(modo.value) & set("wax+"))


if __name__ == "__main__":
    unittest.main()
