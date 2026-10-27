"""Reejecuta notebooks compuestos solo por Python cuando Jupyter no inicia.

Este ejecutor no admite magias ni widgets. Captura texto y tablas mostradas
con ``display``; no reemplaza la validación visual posterior en VS Code.
"""

from argparse import ArgumentParser
import ast
import base64
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


def mime(obj) -> dict:
    """Representaciones que entiende el formato de salida de Jupyter."""
    datos = {"text/plain": [repr(obj)]}
    representaciones = (
        ("text/html", "_repr_html_"),
        ("image/svg+xml", "_repr_svg_"),
        ("image/png", "_repr_png_"),
        ("image/jpeg", "_repr_jpeg_"),
        ("application/json", "_repr_json_"),
    )
    for tipo, metodo in representaciones:
        funcion = getattr(obj, metodo, None)
        if not callable(funcion):
            continue
        valor = funcion()
        if valor is None:
            continue
        # Algunas representaciones devuelven (datos, metadatos).
        if isinstance(valor, tuple):
            valor = valor[0]
        if isinstance(valor, bytes):
            valor = base64.b64encode(valor).decode("ascii")
        datos[tipo] = [valor] if isinstance(valor, str) else valor
    return datos


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    args = parser.parse_args()
    archivo = args.notebook.resolve()
    assert archivo.is_relative_to(RAIZ / "05_notebooks")
    documento = json.loads(archivo.read_text(encoding="utf-8"))
    assert documento["nbformat"] == 4
    contexto: dict = {"__name__": "__main__"}
    numero = 0
    for celda in documento["cells"]:
        if celda["cell_type"] != "code":
            continue
        codigo = "".join(celda["source"])
        assert not any(linea.lstrip().startswith(("%", "!")) for linea in codigo.splitlines()), (
            "No se admiten magias de IPython ni comandos de shell"
        )
        numero += 1
        salidas: list[dict] = []

        def display(*objetos) -> None:
            for obj in objetos:
                salidas.append({"output_type": "display_data", "data": mime(obj), "metadata": {}})

        contexto["display"] = display
        # Permite que ``from IPython.display import display`` dentro del
        # notebook use el capturador anterior, también para imágenes.
        import IPython.display as ipython_display

        ipython_display.display = display
        stdout = StringIO()
        stderr = StringIO()
        try:
            arbol = ast.parse(codigo, filename=f"{archivo.name}:celda_{numero}")
            ultima = arbol.body[-1] if arbol.body and isinstance(arbol.body[-1], ast.Expr) else None
            instrucciones = ast.Module(
                body=arbol.body[:-1] if ultima else arbol.body,
                type_ignores=[],
            )
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(compile(instrucciones, f"{archivo.name}:celda_{numero}", "exec"), contexto)
                valor = (
                    eval(compile(ast.Expression(ultima.value), f"{archivo.name}:celda_{numero}", "eval"), contexto)
                    if ultima else None
                )
        except Exception as exc:
            raise RuntimeError(f"Falló la celda {numero} ({celda.get('id')}): {exc}") from exc
        texto = stdout.getvalue()
        errores = stderr.getvalue()
        if texto:
            salidas.insert(0, {"output_type": "stream", "name": "stdout", "text": [texto]})
        if errores:
            salidas.append({"output_type": "stream", "name": "stderr", "text": [errores]})
        if valor is not None:
            salidas.append({
                "output_type": "execute_result",
                "data": mime(valor),
                "metadata": {},
                "execution_count": numero,
            })
        celda["outputs"] = salidas
        celda["execution_count"] = numero
    # Ninguna salida cambia en disco si una celda falla.
    archivo.write_text(json.dumps(documento, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{archivo.name}: {numero} celdas Python ejecutadas sin errores")


if __name__ == "__main__":
    main()
