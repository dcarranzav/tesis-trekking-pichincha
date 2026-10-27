"""Genera perfiles SVG sin depender de Matplotlib."""

from html import escape
from pathlib import Path

import pandas as pd


FECHA = "2026-10-05"
RUTAS = {
    "R001": "Sendero Cumbre Rucu Pichincha",
    "R003": "Sendero Cascada Cóndor Machay",
    "R005": "Sendero Tarabita - Cascada Nambillo",
    "R006": "Sendero al Ilaló",
}


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontró la carpeta principal del proyecto")


def puntos_svg(x, y, izquierda, arriba, ancho, alto, xmin, xmax, ymin, ymax):
    resultado = []
    for valor_x, valor_y in zip(x, y):
        px = izquierda + (valor_x - xmin) / (xmax - xmin) * ancho
        py = arriba + alto - (valor_y - ymin) / (ymax - ymin) * alto
        resultado.append(f"{px:.1f},{py:.1f}")
    return " ".join(resultado)


proyecto = localizar_proyecto()
carpeta_datos = proyecto / "04_datos_procesados" / "perfiles"
carpeta_salida = proyecto / "07_resultados" / "perfiles"
carpeta_salida.mkdir(parents=True, exist_ok=True)

for id_ruta, nombre in RUTAS.items():
    archivo = carpeta_datos / f"{id_ruta}_perfil_elevacion_procesado_{FECHA}.csv"
    perfil = pd.read_csv(archivo)
    x = perfil["distancia_m"] / 1000
    raw = perfil["elevacion_m"]
    filtrada = perfil["elevacion_mediana3_m"]

    xmin, xmax = 0.0, float(x.max())
    margen_y = max(20.0, float(raw.max() - raw.min()) * 0.08)
    ymin = float(min(raw.min(), filtrada.min()) - margen_y)
    ymax = float(max(raw.max(), filtrada.max()) + margen_y)
    izquierda, arriba, ancho, alto = 85, 70, 850, 340
    ancho_total, alto_total = 1000, 500

    raw_pts = puntos_svg(x, raw, izquierda, arriba, ancho, alto, xmin, xmax, ymin, ymax)
    filtrada_pts = puntos_svg(
        x, filtrada, izquierda, arriba, ancho, alto, xmin, xmax, ymin, ymax
    )

    lineas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho_total}" height="{alto_total}" viewBox="0 0 {ancho_total} {alto_total}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{ancho_total/2}" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">{escape(id_ruta + " – " + nombre)}</text>',
        f'<text x="{ancho_total/2}" y="52" text-anchor="middle" font-family="Arial" font-size="13">Perfil Copernicus DEM GLO-30 · muestreo cada 30 m</text>',
    ]

    for i in range(6):
        valor = ymin + (ymax - ymin) * i / 5
        py = arriba + alto - alto * i / 5
        lineas.append(f'<line x1="{izquierda}" y1="{py:.1f}" x2="{izquierda+ancho}" y2="{py:.1f}" stroke="#dddddd"/>')
        lineas.append(f'<text x="{izquierda-10}" y="{py+4:.1f}" text-anchor="end" font-family="Arial" font-size="11">{valor:.0f}</text>')

    for i in range(6):
        valor = xmax * i / 5
        px = izquierda + ancho * i / 5
        lineas.append(f'<line x1="{px:.1f}" y1="{arriba}" x2="{px:.1f}" y2="{arriba+alto}" stroke="#eeeeee"/>')
        lineas.append(f'<text x="{px:.1f}" y="{arriba+alto+22}" text-anchor="middle" font-family="Arial" font-size="11">{valor:.1f}</text>')

    lineas.extend(
        [
            f'<polyline points="{raw_pts}" fill="none" stroke="#999999" stroke-width="1.5" opacity="0.8"/>',
            f'<polyline points="{filtrada_pts}" fill="none" stroke="#1769aa" stroke-width="2.5"/>',
            f'<line x1="{izquierda}" y1="{arriba+alto}" x2="{izquierda+ancho}" y2="{arriba+alto}" stroke="#333333"/>',
            f'<line x1="{izquierda}" y1="{arriba}" x2="{izquierda}" y2="{arriba+alto}" stroke="#333333"/>',
            f'<text x="{izquierda+ancho/2}" y="{alto_total-20}" text-anchor="middle" font-family="Arial" font-size="13">Distancia de ida (km)</text>',
            f'<text x="20" y="{arriba+alto/2}" text-anchor="middle" transform="rotate(-90 20 {arriba+alto/2})" font-family="Arial" font-size="13">Elevación (m)</text>',
            f'<line x1="{izquierda+580}" y1="{arriba+15}" x2="{izquierda+620}" y2="{arriba+15}" stroke="#999999" stroke-width="2"/><text x="{izquierda+630}" y="{arriba+19}" font-family="Arial" font-size="12">Raw</text>',
            f'<line x1="{izquierda+700}" y1="{arriba+15}" x2="{izquierda+740}" y2="{arriba+15}" stroke="#1769aa" stroke-width="3"/><text x="{izquierda+750}" y="{arriba+19}" font-family="Arial" font-size="12">Mediana 3</text>',
            '</svg>',
        ]
    )

    archivo_salida = carpeta_salida / f"{id_ruta}_perfil_elevacion_{FECHA}.svg"
    archivo_salida.write_text("\n".join(lineas), encoding="utf-8")
    print("Perfil guardado:", archivo_salida.name)
