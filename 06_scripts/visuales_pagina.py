"""Componentes visuales de la página (HTML y SVG, solo biblioteca estándar).

Cada función devuelve una cadena sin sangrías ni líneas en blanco, para que Markdown de Streamlit
no la interprete como bloque de código. Los colores usan variables CSS definidas en app.py y
`currentColor`, de modo que funcionan en tema claro y oscuro. Ningún componente calcula categorías:
solo dibuja valores que ya vienen de `vista_rutas.dificultad_fisica_estimada()`.

Los niveles se distinguen por texto y por el número de barras del indicador, no solo por el color.
"""

from __future__ import annotations

import math
from html import escape

NIVELES = ("Fácil", "Moderada", "Difícil")
COLOR_NIVEL = {"Fácil": "#1f7a5c", "Moderada": "#b7791f", "Difícil": "#b4442f"}
COLOR_RUTA = "#0f5f73"
COLOR_AGUA = "#2f6fa3"
UMBRALES_H = (1.0, 3.0)  # límites de la regla archivada; solo se dibujan, no se calculan


def numero(valor, decimales: int = 1) -> str:
    """Formato español con coma decimal y espacio como separador de miles."""
    texto = f"{float(valor):,.{decimales}f}"
    return texto.replace(",", " ").replace(".", ",")


def _compacto(html: str) -> str:
    return "".join(linea.strip() for linea in html.splitlines())


# ------------------------------------------------------------------ iconos de datos (trazo, 24x24)
_ICONOS = {
    "distancia": '<circle cx="5" cy="18" r="2"/><circle cx="19" cy="6" r="2"/><path d="M7 17c5-1 1-6 6-6s3-4 4-4" fill="none"/>',
    "subida": '<path d="M4 18l6-6 4 4 6-8M15 8h5v5" fill="none"/>',
    "bajada": '<path d="M4 6l6 6 4-4 6 8M15 16h5v-5" fill="none"/>',
    "altitud": '<path d="M3 19l6-11 4 7 3-4 5 8z" fill="none"/>',
    "horas": '<circle cx="12" cy="12" r="8" fill="none"/><path d="M12 7v5l3 2" fill="none"/>',
}


def icono(nombre: str, tam: int = 20) -> str:
    return (f'<svg viewBox="0 0 24 24" width="{tam}" height="{tam}" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_ICONOS[nombre]}</svg>')


def teselas(items: list[tuple[str, str, str, str]]) -> str:
    """Datos clave de una ruta: (icono, valor, unidad, etiqueta)."""
    partes = ['<div class="kpis">']
    for nombre, valor, unidad, etiqueta in items:
        partes.append(
            f'<div class="kpi"><span class="kpi-ico">{icono(nombre)}</span>'
            f'<span class="kpi-val">{escape(valor)}<small> {escape(unidad)}</small></span>'
            f'<span class="kpi-et">{escape(etiqueta)}</span></div>'
        )
    partes.append("</div>")
    return "".join(partes)


def avisos_ruta(altitud: list[str], acceso: list[str], caracter_tecnico: list[str]) -> str:
    """Avisos con prioridad visual para acceso; los bloques breves se apilan a un lado."""
    def tarjeta(titulo: str, avisos: list[str], clase: str = "") -> str:
        contenido = ("<ul>" + "".join(f"<li>{escape(str(aviso))}</li>" for aviso in avisos) + "</ul>"
                     if avisos else "<p>Sin avisos adicionales.</p>")
        return f'<section class="aviso-card {clase}"><h5>{escape(titulo)}</h5>{contenido}</section>'

    return _compacto(
        '<div class="avisos-grid">'
        + tarjeta("Acceso y estado", acceso, "aviso-acceso")
        + '<div class="avisos-lateral">'
        + tarjeta("Altitud", altitud)
        + tarjeta("Carácter técnico", caracter_tecnico)
        + "</div></div>"
    )


# ------------------------------------------------------------------ nivel de dificultad física estimada
def _barras_nivel(nivel: str) -> str:
    n = NIVELES.index(nivel) + 1
    color = COLOR_NIVEL[nivel]
    barras = "".join(
        f'<rect x="{i * 6}" y="{10 - 4 * i - 2 + 2}" width="4" height="{4 * i + 2}" rx="1" '
        f'fill="{color if i < n else "currentColor"}" fill-opacity="{1 if i < n else .22}"/>'
        for i in range(3)
    )
    return f'<svg class="nivel-barras" viewBox="0 0 16 12" width="18" height="14" aria-hidden="true">{barras}</svg>'


def insignia_nivel(nivel: str, sensible: bool = False, rotulo: bool = True) -> str:
    """Una sola etiqueta principal: «Dificultad física estimada: Fácil/Moderada/Difícil»."""
    if nivel not in NIVELES:
        raise ValueError("Nivel desconocido")
    color = COLOR_NIVEL[nivel]
    pre = '<span class="ins-pre">Nivel de esfuerzo:</span> ' if rotulo else ""
    sens = ('<span class="ins-sens" title="Este nivel puede variar si cambian los supuestos del cálculo">'
            'puede variar</span>') if sensible else ""
    return (f'<span class="insignia" style="--c:{color}">{_barras_nivel(nivel)}{pre}<b>{escape(nivel)}</b></span>{sens}')


def tarjeta_ruta(nombre: str, lugar: str, nivel: str, distancia_km, ascenso_m, tipo: str,
                 aviso: str = "", seleccionada: bool = False) -> str:
    """Tarjeta de altura fija dentro de una rejilla: el área de aviso siempre existe, aunque esté vacía."""
    clase = "tarjeta sel" if seleccionada else "tarjeta"
    return _compacto(
        f'<div class="{clase}"><div class="t-lugar">{escape(lugar)}</div><div class="t-nombre">{escape(nombre)}</div>'
        f'<div class="t-nivel">{insignia_nivel(nivel, rotulo=False)}</div>'
        f'<div class="t-datos"><span>{icono("distancia", 16)}{numero(distancia_km, 2)} km</span>'
        f'<span>{icono("subida", 16)}{numero(ascenso_m, 0)} m</span></div>'
        f'<div class="t-tipo">{escape(tipo)}</div>'
        f'<div class="t-aviso">{escape(aviso)}</div></div>'
    )


def portada_marketing(conteos: dict[str, int]) -> str:
    """Texto de bienvenida de «Explorar rutas»: promesa, llamada a la acción y tres ventajas reales de la página.

    Los conteos por nivel vienen de la clasificación archivada y aquí solo se muestran. No usa valoraciones, popularidad
    ni afirmaciones sobre calidad: lo que se promete es lo que la página hace (niveles para las 20 rutas, mapa,
    perfil, simulación del recorrido y entrada sin cuenta).
    """
    total = sum(conteos.values())
    chips = "".join(f'<li style="--c:{COLOR_NIVEL[n]}"><b>{conteos.get(n, 0)}</b><span>{n}</span></li>' for n in NIVELES)
    ventajas = (
        ("Encuentra tu ritmo", "Compara distancia, subida y nivel de esfuerzo entre %d rutas." % total),
        ("Recórrela antes de caminarla", "Simulación de ida y vuelta sobre el mapa, con el perfil de altura en movimiento."),
        ("Entra en segundos", "Escribe un apodo y explora. Sin cuentas ni contraseñas."),
    )
    cajas = "".join(f'<div><b>{escape(t)}</b><span>{escape(d)}</span></div>' for t, d in ventajas)
    return _compacto(
        f'<section class="pf" aria-label="Rutas de trekking en Pichincha">'
        f'<p class="pf-eyebrow">Trekking en Pichincha</p>'
        f'<p class="pf-titulo">Descubre tu próxima caminata en Pichincha</p>'
        f'<p class="pf-sub">Explora {total} rutas, compara la distancia y la subida, y conoce cada recorrido '
        f'en el mapa antes de salir.</p>'
        f'<div class="pf-cta"><a class="pf-boton" href="#elige-una-ruta">Explorar las {total} rutas</a>'
        f'<ul class="pf-niveles" aria-label="Rutas por nivel de dificultad">{chips}</ul></div></section>'
        f'<div class="pf-ventajas">{cajas}</div>'
    )


def galeria_interactiva(fotos: list[dict]) -> str:
    """Galería con controles CSS: flechas, miniaturas y radios accesibles por teclado.

    Streamlit puede eliminar los scripts incrustados en ``st.html``. Los radios
    mantienen sincronizadas la foto, la miniatura y el contador sin JavaScript.
    Las fotos son decorativas y no se asocian a una ruta concreta.
    """
    if not fotos:
        return ""
    total = len(fotos)
    radios = "".join(
        f'<input class="gal-radio" type="radio" name="gal-foto" id="gal-foto-{k}" '
        f'aria-label="Fotografía {k + 1} de {total}"{" checked" if k == 0 else ""}>'
        for k in range(total)
    )
    diapos = "".join(
        f'<div class="gal-slide fo fo-{f["id"]}" role="img" aria-label="{escape(f["alt"])}"></div>'
        for f in fotos)
    flechas = "".join(
        f'<label class="gal-nav gal-ant gal-nav-{k}" for="gal-foto-{(k - 1) % total}" '
        f'aria-label="Fotografía anterior">&#8249;</label>'
        f'<label class="gal-nav gal-sig gal-nav-{k}" for="gal-foto-{(k + 1) % total}" '
        f'aria-label="Fotografía siguiente">&#8250;</label>'
        for k in range(total)
    )
    cuentas = "".join(
        f'<span class="gal-cuenta gal-cuenta-{k}" aria-hidden="true">{k + 1} / {total}</span>'
        for k in range(total)
    )
    minis = "".join(
        f'<label class="gal-mini fo fo-{f["id"]}" for="gal-foto-{k}" '
        f'aria-label="Ver la fotografía {k + 1} de {total}"></label>'
        for k, f in enumerate(fotos)
    )
    estilos = "".join(
        f'.gal-radio:nth-of-type({k + 1}):checked~.gal-escena .gal-slide:nth-child({k + 1})'
        '{opacity:1;animation:gal-kb 9s ease-out forwards}'
        f'.gal-radio:nth-of-type({k + 1}):checked~.gal-escena .gal-nav-{k}'
        '{display:flex}'
        f'.gal-radio:nth-of-type({k + 1}):checked~.gal-escena .gal-cuenta-{k}'
        '{display:block}'
        f'.gal-radio:nth-of-type({k + 1}):checked~.gal-minis .gal-mini:nth-child({k + 1})'
        '{opacity:1;border-color:#fff}'
        for k in range(total)
    )
    return (
        f'<style>{estilos}</style>'
        f'<div class="gal" role="region" aria-roledescription="galería" aria-label="Galería de fotografías de senderos">'
        f'{radios}<div class="gal-escena">{diapos}{flechas}{cuentas}</div>'
        f'<div class="gal-minis">{minis}</div></div>'
    )


def rejilla(tarjetas: list[str], columnas: int = 3) -> str:
    """Rejilla de tarjetas de igual altura: 3 columnas por defecto, 2 para destinos con dos alternativas."""
    return f'<div class="rejilla n{columnas}">' + "".join(tarjetas) + "</div>"


def escala_esfuerzo(horas: float, nivel: str, maximo: float = 5.0) -> str:
    """Dónde cae la ruta respecto a los límites de la regla (1 h y 3 h estimadas)."""
    pos = lambda h: min(100.0, max(0.0, 100 * h / maximo))
    return _compacto(
        f'<div class="escala" role="img" aria-label="{escape(nivel)}: {numero(horas, 2)} horas estimadas de esfuerzo; límites en 1 y 3 horas">'
        f'<div class="escala-pista"><span class="escala-tramo" style="left:0;width:{pos(UMBRALES_H[0]):.1f}%;--c:{COLOR_NIVEL["Fácil"]}"></span>'
        f'<span class="escala-tramo" style="left:{pos(UMBRALES_H[0]):.1f}%;width:{pos(UMBRALES_H[1]) - pos(UMBRALES_H[0]):.1f}%;--c:{COLOR_NIVEL["Moderada"]}"></span>'
        f'<span class="escala-tramo" style="left:{pos(UMBRALES_H[1]):.1f}%;width:{100 - pos(UMBRALES_H[1]):.1f}%;--c:{COLOR_NIVEL["Difícil"]}"></span>'
        f'<span class="escala-marca" style="left:{pos(horas):.1f}%"></span></div>'
        f'<div class="escala-et"><span style="left:0">0 h</span><span style="left:{pos(UMBRALES_H[0]):.1f}%">1 h</span>'
        f'<span style="left:{pos(UMBRALES_H[1]):.1f}%">3 h</span><span style="left:100%">{numero(maximo, 0)} h o más</span></div>'
        f'<div class="escala-niv"><span style="left:{pos(UMBRALES_H[0]) / 2:.1f}%">Fácil</span>'
        f'<span style="left:{(pos(UMBRALES_H[0]) + pos(UMBRALES_H[1])) / 2:.1f}%">Moderada</span>'
        f'<span style="left:{(pos(UMBRALES_H[1]) + 100) / 2:.1f}%">Difícil</span></div></div>'
    )


def resumen_niveles(conteos: dict[str, int]) -> str:
    total = sum(conteos.values()) or 1
    segmentos = "".join(
        f'<span class="apilada-seg" style="width:{100 * conteos.get(n, 0) / total:.1f}%;--c:{COLOR_NIVEL[n]}"></span>' for n in NIVELES)
    leyenda = "".join(
        f'<div class="apilada-item"><span class="apilada-n" style="--c:{COLOR_NIVEL[n]}">{conteos.get(n, 0)}</span>'
        f'<span>{_barras_nivel(n)} {escape(n)}</span></div>' for n in NIVELES)
    return _compacto(f'<div class="apilada">{segmentos}</div><div class="apilada-lista">{leyenda}</div>')


def grafico_horas(rutas: list[dict]) -> str:
    """Horas de referencia como contraste, coloreadas con el grupo K-means."""
    if not rutas:
        return ""
    maximo = max(5.0, math.ceil(max(float(r["horas"]) for r in rutas)))
    pos = lambda h: 100 * h / maximo
    filas = []
    for r in sorted(rutas, key=lambda r: (float(r["horas"]), r["nombre"])):
        color = COLOR_NIVEL[r["nivel"]]
        sens = " *" if r.get("sensible") else ""
        filas.append(
            f'<div class="hg-fila"><span class="hg-nombre" title="{escape(r["nombre"])}">{escape(r["nombre"])}</span>'
            f'<span class="hg-pista"><span class="hg-barra" style="width:{max(1.5, pos(float(r["horas"]))):.1f}%;--c:{color}"></span></span>'
            f'<span class="hg-val">{numero(r["horas"], 2)} h · {escape(r["nivel"])}{sens}</span></div>'
        )
    leyenda = ('<div class="hg-leyenda">Longitud de la barra: horas de referencia estimadas; color: grupo K-means. '
               'Las horas no determinan el grupo. * Asignación sensible en alguna prueba del modelo.</div>')
    return _compacto('<div class="hg">' + "".join(filas) + "</div>" + leyenda)


# ------------------------------------------------------------------ perfil en miniatura y barras
def miniperfil(elevaciones: list[float], color: str = COLOR_RUTA, ancho: int = 260, alto: int = 56) -> str:
    """Área con la silueta de elevación de la ruta (sin ejes: el perfil completo está en el visor)."""
    valores = [float(e) for e in elevaciones if math.isfinite(float(e))]
    if len(valores) < 2:
        return ""
    paso = max(1, len(valores) // 70)
    valores = valores[::paso] + ([valores[-1]] if (len(valores) - 1) % paso else [])
    lo, hi = min(valores), max(valores)
    rango = (hi - lo) or 1.0
    n = len(valores)
    puntos = [(2 + (ancho - 4) * i / (n - 1), 4 + (alto - 14) * (1 - (v - lo) / rango)) for i, v in enumerate(valores)]
    linea = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    area = f"2,{alto - 6} {linea} {ancho - 2},{alto - 6}"
    return _compacto(
        f'<svg class="mini" viewBox="0 0 {ancho} {alto}" preserveAspectRatio="none" role="img" '
        f'aria-label="Silueta de elevación: de {lo:.0f} a {hi:.0f} metros">'
        f'<polygon points="{area}" fill="{color}" fill-opacity=".18"/>'
        f'<polyline points="{linea}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>'
        '</svg>'
    )


def barras_relativas(filas: list[dict], campo: str, titulo: str, unidad: str, decimales: int = 1) -> str:
    """Barras horizontales de las alternativas de un mismo destino (etiqueta y valor)."""
    maximo = max((float(f[campo]) for f in filas), default=0) or 1.0
    partes = [f'<div class="barras"><div class="barras-t">{escape(titulo)}</div>']
    for f in filas:
        v = float(f[campo])
        partes.append(
            f'<div class="barra-fila"><span class="barra-id" title="{escape(f["etiqueta"])}">{escape(f["etiqueta"])}</span>'
            f'<span class="barra-pista"><span class="barra-relleno" style="width:{max(3.0, 100 * v / maximo):.1f}%"></span></span>'
            f'<span class="barra-val">{numero(v, decimales)} {escape(unidad)}</span></div>'
        )
    partes.append("</div>")
    return "".join(partes)


# ------------------------------------------------------------------ clima: iconos y esquema de la ruta
def icono_clima(condicion: str, tam: int = 64) -> str:
    sol = ('<circle cx="32" cy="32" r="10" fill="#f5b301"/>' + "".join(
        f'<line x1="{32 + 15 * math.cos(a):.1f}" y1="{32 + 15 * math.sin(a):.1f}" x2="{32 + 21 * math.cos(a):.1f}" '
        f'y2="{32 + 21 * math.sin(a):.1f}" stroke="#f5b301" stroke-width="3" stroke-linecap="round"/>'
        for a in [i * math.pi / 4 for i in range(8)]))
    nube = '<path d="M18 46h28a9 9 0 0 0 .5-18 13 13 0 0 0-25-3A10.5 10.5 0 0 0 18 46z" fill="#cbd5e1"/>'
    nube_osc = nube.replace("#cbd5e1", "#94a3b8")
    gotas = "".join(f'<line x1="{x}" y1="50" x2="{x - 3}" y2="58" stroke="{COLOR_AGUA}" stroke-width="3" stroke-linecap="round"/>' for x in (24, 33, 42))
    llovizna = "".join(f'<line x1="{x}" y1="51" x2="{x - 2}" y2="56" stroke="{COLOR_AGUA}" stroke-width="2.5" stroke-linecap="round"/>' for x in (24, 33, 42))
    nieve = "".join(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#e2e8f0" stroke="#94a3b8"/>' for x, y in ((24, 54), (33, 58), (42, 54)))
    rayo = '<polygon points="34,44 26,56 32,56 29,64 40,50 34,50" fill="#f5b301"/>'
    niebla = "".join(f'<line x1="{a}" y1="{y}" x2="{b}" y2="{y}" stroke="#94a3b8" stroke-width="3" stroke-linecap="round"/>' for a, b, y in ((14, 50, 51), (20, 56, 57)))
    c = condicion
    if c == "Despejado":
        cuerpo = sol
    elif c == "Nubosidad variable":
        cuerpo = ('<g transform="translate(-8 -8) scale(.75) translate(8 8)">' + sol + "</g>"
                  '<g transform="translate(6 2)">' + nube + "</g>")
    elif c == "Niebla":
        cuerpo = nube + niebla
    elif c == "Llovizna":
        cuerpo = nube + llovizna
    elif c == "Lluvia":
        cuerpo = nube_osc + gotas
    elif c == "Nieve":
        cuerpo = nube + nieve
    elif c == "Tormenta":
        cuerpo = nube_osc + rayo
    else:
        cuerpo = nube
    return (f'<svg viewBox="0 0 64 64" width="{tam}" height="{tam}" role="img" aria-label="{escape(c)}">{cuerpo}</svg>')


_ICONO_VIENTO = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" '
                 'stroke-linecap="round" aria-hidden="true"><path d="M3 8h11a3 3 0 1 0-3-3M3 13h16a3 3 0 1 1-3 3M3 18h7"/></svg>')
_ICONO_GOTA = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" '
               'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/></svg>')
_ICONO_TERMO = ('<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" '
                'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 14V5a2 2 0 0 1 4 0v9a4 4 0 1 1-4 0z"/></svg>')




def _mapa_trazado(perfil: list[dict], puntos: list[dict], ancho: int = 360, alto: int = 230) -> str:
    lat0 = sum(float(p["lat"]) for p in perfil) / len(perfil)
    k = math.cos(math.radians(lat0))
    xs = [float(p["lon"]) * k for p in perfil]
    ys = [float(p["lat"]) for p in perfil]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    esc = min((ancho - 70) / ((x1 - x0) or 1e-6), (alto - 70) / ((y1 - y0) or 1e-6))
    ox = (ancho - esc * (x1 - x0)) / 2
    oy = (alto - esc * (y1 - y0)) / 2
    pr = lambda lon, lat: (ox + esc * (float(lon) * k - x0), alto - oy - esc * (float(lat) - y0))
    paso = max(1, len(perfil) // 90)
    linea = " ".join("%.1f,%.1f" % pr(p["lon"], p["lat"]) for p in perfil[::paso])
    partes = [f'<svg class="mapa-clima" viewBox="0 0 {ancho} {alto}" role="img" aria-label="Esquema del recorrido con los dos puntos consultados">',
              f'<rect width="{ancho}" height="{alto}" rx="14" fill="currentColor" fill-opacity=".05"/>']
    for i in range(1, 6):  # retícula suave, sugiere mapa
        partes.append(f'<line x1="{i * ancho / 6:.0f}" x2="{i * ancho / 6:.0f}" y1="0" y2="{alto}" stroke="currentColor" stroke-opacity=".07"/>')
    for i in range(1, 4):
        partes.append(f'<line y1="{i * alto / 4:.0f}" y2="{i * alto / 4:.0f}" x1="0" x2="{ancho}" stroke="currentColor" stroke-opacity=".07"/>')
    partes.append(f'<polyline points="{linea}" fill="none" stroke="#0b132b" stroke-opacity=".35" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>')
    partes.append(f'<polyline points="{linea}" fill="none" stroke="{COLOR_RUTA}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    for punto in puntos:
        x, y = pr(punto["lon"], punto["lat"])
        ancla = "start" if x < ancho / 2 else "end"
        dx = 16 if x < ancho / 2 else -16
        col = COLOR_RUTA
        partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{col}" stroke="#fff" stroke-width="2.5"/>')
        partes.append(f'<text x="{x + dx:.1f}" y="{y + 4:.1f}" font-size="13" font-weight="600" text-anchor="{ancla}" fill="currentColor" opacity=".9">{escape(str(punto["nombre"]))}</text>')
    partes.append("</svg>")
    return "".join(partes)



def _fila_dato(icono_svg: str, etiqueta: str, valor: str) -> str:
    return (f'<div class="clima-dato"><span class="clima-dato-et">{icono_svg}{escape(etiqueta)}</span>'
            f'<span class="clima-dato-val">{valor}</span></div>')


def panel_clima(perfil: list[dict], puntos: list[dict]) -> str:
    """Esquema del recorrido y una tarjeta por punto. Temperatura, precipitación y viento van por separado:
    la temperatura no se traduce en una etiqueta (calor/frío) ni se mezcla con la condición del cielo."""
    tarjetas = []
    for p in puntos:
        hora = escape(str(p["hora_local"]).replace("T", " "))
        tarjetas.append(
            f'<div class="clima-tarjeta"><div class="clima-cab">{escape(str(p["nombre"]))}'
            f'<small>{float(p["lat"]):.4f}, {float(p["lon"]):.4f} · altitud del trazado {numero(p.get("elev", 0), 0)} m</small></div>'
            f'<div class="clima-cond">{icono_clima(str(p["condicion"]), 44)}<span><small>Tiempo estimado</small>{escape(str(p["condicion"]))}</span></div>'
            + _fila_dato(_ICONO_TERMO, "Temperatura", f'{numero(p["temperatura_c"], 1)} °C')
            + _fila_dato(_ICONO_GOTA, "Precipitación", f'{numero(p["precipitacion_mm"], 1)} mm')
            + _fila_dato(_ICONO_VIENTO, "Viento", f'{numero(p["viento_kmh"], 0)} km/h')
            + f'<div class="clima-hora">Válido: {hora} (hora de Ecuador)</div></div>'
        )
    return ('<div class="clima">' + f'<div class="clima-mapa">{_mapa_trazado(perfil, puntos)}</div>'
            + '<div class="clima-lista">' + "".join(tarjetas) + "</div></div>")


# ------------------------------------------------------------------ pasos del método
def flujo(pasos: list[tuple[str, str]]) -> str:
    partes = ['<div class="flujo">']
    for i, (titulo, texto) in enumerate(pasos, 1):
        partes.append(f'<div class="flujo-paso"><span class="flujo-n">{i}</span><b>{escape(titulo)}</b><span>{escape(texto)}</span></div>')
    partes.append("</div>")
    return "".join(partes)


def tabla_html(encabezados: list[str], filas: list[list[str]]) -> str:
    """Tabla simple; las celdas ya vienen como HTML seguro (se escapan en quien llama)."""
    cab = "".join(f"<th>{escape(h)}</th>" for h in encabezados)
    cuerpo = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in fila) + "</tr>" for fila in filas)
    return f'<div class="tabla-wrap"><table class="tabla"><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table></div>'
