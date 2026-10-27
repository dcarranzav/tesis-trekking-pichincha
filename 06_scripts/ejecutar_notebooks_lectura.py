"""Actualiza las salidas de notebooks de consulta en el Python del proyecto.

Ejecuta celdas Python en orden y guarda el .ipynb solo si todas finalizan bien.
Los cinco notebooks permitidos son de lectura y no requieren magics de Jupyter.
"""

import ast
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import os
from pathlib import Path
import sys

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


def mime(valor):
    datos = {"text/plain": repr(valor)}
    html = getattr(valor, "_repr_html_", None)
    if callable(html):
        datos["text/html"] = html()
    return datos


def ejecutar(nombre: str) -> None:
    archivo = NOTEBOOKS / nombre
    notebook = nbformat.read(archivo, as_version=4)
    contexto = {"__name__": "__main__"}
    cuenta = 0
    for celda in notebook.cells:
        if celda.cell_type != "code":
            continue
        cuenta += 1
        arbol = ast.parse(celda.source, filename=f"{nombre}:{cuenta}")
        if not arbol.body:
            celda.outputs = []
            celda.execution_count = cuenta
            continue
        mostrados = []

        def display_local(*valores):
            for valor in valores:
                mostrados.append(nbformat.v4.new_output("display_data", data=mime(valor)))

        contexto["display"] = display_local
        salida, errores = StringIO(), StringIO()
        ultima = arbol.body[-1] if isinstance(arbol.body[-1], ast.Expr) else None
        instrucciones = ast.Module(body=arbol.body[:-1] if ultima else arbol.body, type_ignores=[])
        with redirect_stdout(salida), redirect_stderr(errores):
            exec(compile(instrucciones, f"{nombre}:{cuenta}", "exec"), contexto)
            valor = eval(compile(ast.Expression(ultima.value), f"{nombre}:{cuenta}", "eval"), contexto) if ultima else None
        outputs = []
        if salida.getvalue():
            outputs.append(nbformat.v4.new_output("stream", name="stdout", text=salida.getvalue()))
        if errores.getvalue():
            outputs.append(nbformat.v4.new_output("stream", name="stderr", text=errores.getvalue()))
        outputs.extend(mostrados)
        if valor is not None:
            outputs.append(nbformat.v4.new_output("execute_result", data=mime(valor), execution_count=cuenta))
        celda.outputs = outputs
        celda.execution_count = cuenta
    nbformat.validate(notebook)
    nbformat.write(notebook, archivo)
    print(f"{nombre}: {cuenta} celdas ejecutadas sin errores", flush=True)


if __name__ == "__main__":
    os.chdir(RAIZ)
    gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
    if gdal_data.exists():
        os.environ["GDAL_DATA"] = str(gdal_data)
    for seleccionado in PERMITIDOS:
        ejecutar(seleccionado)
