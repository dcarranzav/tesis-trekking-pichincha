"""Punto de entrada ligero para alojar la interfaz en Streamlit Community Cloud.

La investigación usa environment.yml en la raíz; este archivo permite que el
alojamiento elija web/requirements.txt y no instale el entorno geoespacial.
"""

from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parents[1] / "app.py"), run_name="__main__")
