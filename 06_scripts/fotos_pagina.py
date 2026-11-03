"""Fotografías de la portada de «Explorar rutas» (solo biblioteca estándar).

Las imágenes viven en `assets/fotos/` (versiones web de las fotografías del autor; los originales no se modifican).
Se incrustan como imágenes de fondo CSS en base64, de modo que funcionan igual con `streamlit run app.py` y en el
despliegue, sin servir archivos estáticos ni depender de rutas de la computadora del autor. Forman la galería interactiva de la
portada (no se asocian a rutas concretas) y las tarjetas de ruta no llevan fotografía. Si un archivo falta, el recuadro
queda con un degradado y la portada sigue siendo legible.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

CARPETA = Path(__file__).resolve().parents[1] / "assets" / "fotos"

# `personas`: la imagen muestra personas; confirmar su autorización de uso público antes de publicar la página.
# Son recortes horizontales de 960 x 540 px de las fotografías originales (verticales); `y` centra el encuadre.
FOTOS = (
    {"id": "01", "archivo": "galeria_01.jpg", "personas": True, "y": 50,
     "alt": "Dos excursionistas, de espaldas, caminan por un sendero entre pajonal hacia una montaña con la cumbre entre nubes."},
    {"id": "02", "archivo": "galeria_02.jpg", "personas": False, "y": 50,
     "alt": "Terreno rocoso de montaña con una señal azul y una pared de roca entre la niebla."},
    {"id": "03", "archivo": "galeria_03.jpg", "personas": True, "y": 50,
     "alt": "Varias personas avanzan por un sendero de roca en una ladera empinada bajo una pared rocosa."},
    {"id": "04", "archivo": "galeria_04.jpg", "personas": False, "y": 50,
     "alt": "Cresta montañosa cubierta de vegetación bajo un cielo azul con nubes."},
    {"id": "05", "archivo": "galeria_05.jpg", "personas": True, "y": 50,
     "alt": "Tres excursionistas de espaldas descienden por una ladera de pajonal con un valle al fondo."},
    {"id": "06", "archivo": "galeria_06.jpg", "personas": True, "y": 50,
     "alt": "Silueta de una persona con los brazos abiertos frente al amanecer sobre un mar de nubes."},
)
# Orden de la galería: abre con la imagen sin personas de mayor impacto.
ORDEN = ("04", "01", "02", "06", "03", "05")


def foto_por_id(id_foto: str) -> dict:
    return next(f for f in FOTOS if f["id"] == id_foto)


@lru_cache(maxsize=1)
def css_fotos() -> str:
    """Reglas `.fo-<id>` con la imagen en base64; las fotos que no se puedan leer se omiten sin error."""
    reglas = []
    for f in FOTOS:
        try:
            datos = base64.b64encode((CARPETA / f["archivo"]).read_bytes()).decode("ascii")
        except OSError:
            continue
        reglas.append(f'.fo-{f["id"]}{{background-image:url(data:image/jpeg;base64,{datos});background-position:50% {f["y"]}%}}')
    return "".join(reglas)


def fotos_con_personas() -> list[str]:
    return [f["archivo"] for f in FOTOS if f["personas"]]
