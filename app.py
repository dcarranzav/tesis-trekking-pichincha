"""Rutas de trekking en Pichincha: dificultad física estimada de 20 recorridos.

Ejecutar con `streamlit run app.py`. No usa base de datos ni cuentas: la bienvenida pide un nombre o apodo
para saludar durante la sesión de Streamlit en el servidor. La categoría Fácil/Moderada/Difícil
procede de K-means k=3 sobre distancia y ascenso de las 20 rutas; es relativa y experimental.
No recomienda salidas ni evalúa seguridad, acceso, técnica ni clima.

Secciones: «Explorar rutas» (filtros, tarjetas y ficha con mapa), «Comparar alternativas» (solo rutas que llegan
al mismo destino exacto) y «Metodología y límites». La regla MIDE adaptada, Ward y DBSCAN
se conservan como contrastes metodológicos.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from html import escape
from pathlib import Path
from textwrap import dedent

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "06_scripts"))
import vista_rutas as vr  # noqa: E402
import visuales_pagina as vz  # noqa: E402
import fotos_pagina as fotos  # noqa: E402
import clima_rutas as clima  # noqa: E402

SECCIONES = ("Explorar rutas", "Comparar alternativas", "Cómo funciona")
TODOS = "Todos"
ESCENARIOS = {
    "piso_desfavorable_3_kmh": "caminar a 3 km/h en horizontal (terreno más lento)",
    "piso_favorable_5_kmh": "caminar a 5 km/h en horizontal (terreno más rápido)",
    "dem_crudo": "usar las subidas y bajadas sin filtrar el ruido del modelo de elevación",
    "dem_mediana5": "filtrar el ruido del modelo de elevación con una ventana más amplia",
}
ESCENARIOS_K3 = {
    "peso_distancia_x2": "dar el doble de peso a la distancia (prueba de estrés)",
    "peso_ascenso_x0.5": "dar la mitad de peso a la subida (prueba de estrés)",
    "ascenso_crudo": "calcular la subida con el modelo de elevación sin filtrar el ruido",
    "mas_pendiente_media": "añadir la pendiente media como tercera variable",
}

st.set_page_config(page_title="Rutas de trekking · Pichincha", page_icon=":material/hiking:", layout="wide")

ESTILO = """
:root{--acento:#0f5f73;--borde:rgba(128,128,128,.30);--suave:rgba(128,128,128,.07)}
.bienvenida-esp{height:6vh}
.bienvenida{padding:.3rem 0 0}
.bienvenida .b-sello{font-size:.74rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;opacity:.7;margin:0 0 .5rem}
.bienvenida .b-titulo{font-size:1.75rem;font-weight:750;line-height:1.15;margin:0 0 .5rem;letter-spacing:-.01em}
.bienvenida .b-lema{font-size:1rem;line-height:1.5;opacity:.9;margin:0 0 1.1rem}
.bienvenida .b-datos{list-style:none;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.5rem;padding:0;margin:0 0 .9rem}
.bienvenida .b-datos li{border:1px solid var(--borde);border-radius:8px;padding:.55rem .65rem;display:flex;flex-direction:column;gap:.1rem;margin:0}
.bienvenida .b-datos b{font-size:1.15rem}
.bienvenida .b-datos span{font-size:.78rem;line-height:1.3;opacity:.85}
.stMarkdown p.saludo{margin:0;padding:0;font-size:.95rem;line-height:2.5rem;opacity:.85}

.block-container{padding-top:1.2rem;padding-bottom:2.5rem;max-width:1180px}
h1,h2,h3,h4{letter-spacing:-.01em}
.hero{border:1px solid var(--borde);border-left:6px solid var(--acento);border-radius:10px;padding:1.2rem 1.4rem;margin:.1rem 0 .9rem;background:var(--suave)}
.hero .sello{font-size:.78rem;font-weight:600;letter-spacing:.05em;text-transform:uppercase;opacity:.75;margin:0 0 .35rem}
.hero .titulo{font-size:1.95rem;font-weight:750;line-height:1.15;margin:0 0 .45rem}
.hero .lema{font-size:1.04rem;margin:0;max-width:820px;opacity:.92;line-height:1.5}
.hero .limite{margin:.7rem 0 0;font-size:.9rem;opacity:.85;border-top:1px solid var(--borde);padding-top:.6rem}
.tarjeta.fija{height:14.4rem;min-height:0;overflow:hidden}
.tres{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;margin:0 0 .9rem}
.tres>div{border:1px solid var(--borde);border-radius:10px;padding:.75rem .95rem}
.tres b{display:block;margin-bottom:.15rem;font-size:.95rem}
.tres span{font-size:.9rem;line-height:1.45;opacity:.92}
.insignia{display:inline-flex;align-items:center;gap:.4rem;border-radius:6px;padding:.15rem .6rem;font-size:.85rem;border:1.5px solid var(--c)}
.insignia b{font-weight:700}
.insignia .ins-pre{opacity:.85}
.nivel-barras{flex:none}
.ins-sens{display:inline-block;margin-left:.45rem;font-size:.74rem;font-weight:600;padding:.05rem .45rem;border-radius:6px;border:1px dashed currentColor;opacity:.85}
.rejilla{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;margin:.4rem 0 1rem;grid-auto-rows:1fr}
.rejilla.n2{grid-template-columns:repeat(2,minmax(0,1fr))}
.rejilla.n4{grid-template-columns:repeat(4,minmax(0,1fr))}
.tarjeta{display:flex;flex-direction:column;gap:.35rem;border:1px solid var(--borde);border-radius:10px;padding:.8rem .95rem;min-height:12.2rem}
.tarjeta.sel{border:2px solid var(--acento);padding:calc(.8rem - 1px) calc(.95rem - 1px)}
.t-lugar{font-size:.76rem;text-transform:uppercase;letter-spacing:.04em;opacity:.7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.t-nombre{font-weight:700;line-height:1.25;min-height:2.5em;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.t-datos{display:flex;gap:1.1rem;font-size:.92rem}
.t-datos span{display:inline-flex;align-items:center;gap:.35rem}
.t-tipo{font-size:.8rem;opacity:.7}
.t-aviso{font-size:.8rem;margin-top:auto;min-height:2.4em;opacity:.9;border-top:1px solid var(--borde);padding-top:.35rem}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.7rem;margin:.6rem 0 .7rem}
.kpi{display:flex;flex-direction:column;gap:.1rem;border:1px solid var(--borde);border-radius:10px;padding:.65rem .85rem}
.kpi-ico{color:var(--acento)}
.kpi-val{font-size:1.45rem;font-weight:720;line-height:1.1}
.kpi-val small{font-size:.8rem;font-weight:500;opacity:.8}
.kpi-et{font-size:.82rem;opacity:.8}
.avisos-grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(15rem,.75fr);gap:.8rem;align-items:start;margin:.45rem 0 1rem}
.avisos-lateral{display:grid;gap:.8rem}
.aviso-card{min-width:0;border:1px solid var(--borde);border-radius:10px;padding:.8rem .95rem;font-size:.9rem;line-height:1.5}
.aviso-card h5{font-size:.96rem;margin:0 0 .35rem;font-weight:700}
.aviso-card ul{margin:.2rem 0 0;padding-left:1.15rem}
.aviso-card li{padding-left:.12rem}
.aviso-card li+li{margin-top:.55rem}
.aviso-card p{margin:.2rem 0 0;opacity:.8}
svg.mini{width:100%;height:56px;display:block}
.escala{position:relative;margin:.3rem 0 1.4rem;padding-top:.2rem}
.escala-pista{position:relative;height:.7rem;border-radius:6px;overflow:visible;background:var(--suave)}
.escala-tramo{position:absolute;top:0;bottom:0;background:var(--c);opacity:.75}
.escala-marca{position:absolute;top:-.35rem;width:3px;height:1.4rem;background:currentColor;border-radius:2px;transform:translateX(-50%)}
.escala-et,.escala-niv{position:relative;height:1.1rem;font-size:.76rem;opacity:.8}
.escala-et span,.escala-niv span{position:absolute;transform:translateX(-50%);white-space:nowrap}
.escala-et span:first-child{transform:none}.escala-et span:last-child{transform:translateX(-100%)}
.escala-niv{font-weight:600;opacity:.95}
.apilada{display:flex;height:1rem;border-radius:6px;overflow:hidden;margin:.3rem 0}
.apilada-seg{background:var(--c);display:block}
.apilada-lista{display:flex;flex-wrap:wrap;gap:.4rem 1.6rem;margin:.3rem 0 .6rem}
.apilada-item{display:flex;align-items:center;gap:.5rem}
.apilada-n{font-size:1.6rem;font-weight:750;color:var(--c)}
.hg{margin:.4rem 0}
.hg-fila{display:grid;grid-template-columns:minmax(8rem,17rem) 1fr 8.6rem;gap:.6rem;align-items:center;margin:.2rem 0;font-size:.84rem}
.hg-nombre{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hg-pista{position:relative;height:.65rem;background:var(--suave);border-radius:6px;display:block}
.hg-barra{position:absolute;left:0;top:0;bottom:0;border-radius:6px;background:var(--c)}
.hg-limite{position:absolute;top:-.2rem;bottom:-.2rem;width:0;border-left:1px dashed currentColor;opacity:.55}
.hg-val{font-variant-numeric:tabular-nums;white-space:nowrap}
.hg-leyenda{font-size:.78rem;opacity:.75;margin-top:.3rem}
.barras{margin:.2rem 0 .6rem}
.barras-t{font-weight:650;font-size:.92rem;margin-bottom:.3rem}
.barra-fila{display:grid;grid-template-columns:minmax(6rem,11rem) 1fr 5.8rem;gap:.5rem;align-items:center;margin:.22rem 0;font-size:.85rem}
.barra-id{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.barra-pista{height:.65rem;border-radius:6px;background:var(--suave);overflow:hidden;display:block}
.barra-relleno{display:block;height:100%;border-radius:6px;background:var(--acento)}
.barra-val{text-align:right;font-variant-numeric:tabular-nums}
.clima{display:grid;grid-template-columns:minmax(240px,1fr) 1.4fr;gap:.9rem;align-items:start;margin:.5rem 0}
.clima-mapa svg{width:100%;height:auto;display:block;color:inherit}
.clima-lista{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.7rem}
.clima-tarjeta{border:1px solid var(--borde);border-radius:10px;padding:.75rem .9rem}
.clima-cab{font-weight:700;display:flex;flex-direction:column;margin-bottom:.4rem}
.clima-cab small{font-weight:400;opacity:.7;font-size:.76rem}
.clima-cond{display:flex;align-items:center;gap:.6rem;margin-bottom:.4rem}
.clima-cond small{display:block;font-size:.72rem;opacity:.7}
.clima-dato{display:flex;justify-content:space-between;gap:.6rem;border-top:1px solid var(--borde);padding:.3rem 0;font-size:.9rem}
.clima-dato-et{display:inline-flex;align-items:center;gap:.4rem;opacity:.85}
.clima-dato-val{font-weight:650;font-variant-numeric:tabular-nums}
.clima-hora{font-size:.74rem;opacity:.7;margin-top:.35rem}
.tabla-wrap{overflow-x:auto;margin:.3rem 0 .8rem}
.tabla{border-collapse:collapse;width:100%;font-size:.88rem}
.tabla th{text-align:left;font-weight:650;border-bottom:2px solid var(--borde);padding:.4rem .6rem}
.tabla td{border-bottom:1px solid var(--borde);padding:.38rem .6rem;vertical-align:top}
.flujo{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.7rem;margin:.4rem 0 1rem}
.flujo-paso{border:1px solid var(--borde);border-radius:10px;padding:.7rem .85rem;display:flex;flex-direction:column;gap:.25rem}
.flujo-paso span:last-child{font-size:.86rem;opacity:.9;line-height:1.4}
.flujo-n{display:inline-flex;align-items:center;justify-content:center;width:1.5rem;height:1.5rem;border-radius:50%;background:var(--acento);color:#fff;font-weight:700;font-size:.82rem}
.stMarkdown p,.stMarkdown li,.stMarkdown a,.tabla td{overflow-wrap:anywhere;word-break:break-word}
.fo{background-color:#24404a;background-image:linear-gradient(135deg,#2b4c57,#1b2f37);background-size:cover;background-repeat:no-repeat;background-position:center}
.pf{margin:.3rem 0 1.1rem}
.pf .pf-eyebrow{font-size:.8rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase;color:#5cc4d9;margin:0 0 .5rem}
.pf .pf-titulo{font-size:2.75rem;font-weight:800;line-height:1.07;letter-spacing:-.027em;margin:0 0 .75rem;max-width:46rem}
.pf .pf-sub{font-size:1.12rem;line-height:1.55;opacity:.9;max-width:42rem;margin:0 0 1.15rem}
.pf .pf-cta{display:flex;flex-wrap:wrap;align-items:center;gap:.8rem 1.2rem;margin:0 0 .2rem}
.pf a.pf-boton{display:inline-block;background:#0f5f73;color:#fff!important;font-weight:700;font-size:1.02rem;padding:.72rem 1.4rem;border-radius:999px;text-decoration:none!important;box-shadow:0 6px 18px rgba(15,95,115,.5);transition:transform .15s,background .15s}
.pf a.pf-boton:hover{background:#1384a0;transform:translateY(-1px)}
.pf .pf-niveles{list-style:none;display:flex;flex-wrap:wrap;gap:.5rem;padding:0;margin:0}
.pf .pf-niveles li{display:flex;align-items:baseline;gap:.4rem;margin:0;padding:.28rem .8rem .28rem .7rem;border-radius:999px;border:1px solid var(--borde);border-left:5px solid var(--c)}
.pf .pf-niveles b{font-size:1.1rem}
.pf .pf-niveles span{font-size:.86rem;opacity:.9}
.pf-ventajas{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;margin:0 0 1.2rem}
.pf-ventajas>div{border:1px solid var(--borde);border-radius:12px;padding:.8rem 1rem;display:flex;flex-direction:column;gap:.2rem;background:var(--suave)}
.pf-ventajas b{font-size:.98rem}
.pf-ventajas span{font-size:.88rem;line-height:1.45;opacity:.88}
.gal{position:relative;margin:.2rem 0 1rem;outline:none}
.gal:focus-visible .gal-escena{box-shadow:0 0 0 3px #5cc4d9}
.gal-radio{position:absolute;width:1px;height:1px;opacity:0}
.gal-radio:focus-visible~.gal-escena{box-shadow:0 0 0 3px #5cc4d9}
.gal-escena{position:relative;aspect-ratio:16/7.2;border-radius:16px;overflow:hidden;background:#13232a;box-shadow:0 10px 30px rgba(0,0,0,.35)}
.gal-escena::after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(6,16,22,.5),rgba(6,16,22,0) 42%);pointer-events:none}
.gal-slide{position:absolute;inset:-2%;opacity:0;transition:opacity .9s ease;transform:scale(1.02)}
.gal-slide:nth-child(odd){--dx:-1.6%;--dy:-1%}
.gal-slide:nth-child(even){--dx:1.6%;--dy:1%}
.gal-slide.activa{opacity:1;animation:gal-kb 9s ease-out forwards}
@keyframes gal-kb{from{transform:scale(1.02) translate(0,0)}to{transform:scale(1.12) translate(var(--dx),var(--dy))}}
.gal-nav{position:absolute;top:50%;z-index:3;transform:translateY(-50%);width:2.7rem;height:2.7rem;border-radius:50%;border:1px solid rgba(255,255,255,.35);background:rgba(8,18,24,.55);color:#fff;font-size:1.7rem;line-height:1;cursor:pointer;opacity:0;transition:opacity .2s,background .2s;display:none;align-items:center;justify-content:center}
.gal-ant{left:.8rem}.gal-sig{right:.8rem}
.gal-escena:hover .gal-nav,.gal-nav:focus-visible{opacity:1}
.gal-nav:hover{background:rgba(8,18,24,.85)}
.gal-cuenta{position:absolute;right:.9rem;bottom:.9rem;z-index:3;font-size:.82rem;font-weight:600;color:#fff;background:rgba(8,18,24,.6);padding:.12rem .6rem;border-radius:999px;display:none}
.gal-barra{position:absolute;left:0;right:0;bottom:0;height:3px;z-index:3;background:rgba(255,255,255,.2)}
.gal-barra span{display:block;height:100%;background:#fff;transform-origin:left;transform:scaleX(0);animation:gal-prog 5.5s linear forwards}
@keyframes gal-prog{to{transform:scaleX(1)}}
.gal.en-pausa .gal-barra span,.gal.en-pausa .gal-slide.activa{animation-play-state:paused}
.gal-minis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:.55rem;margin-top:.6rem}
.gal-mini{display:block;aspect-ratio:16/10;border-radius:10px;border:2px solid transparent;padding:0;cursor:pointer;opacity:.6;transition:opacity .2s,transform .2s,border-color .2s}
.gal-mini:hover{opacity:1;transform:translateY(-2px)}
.gal-mini.activa{opacity:1;border-color:#fff}
@media (prefers-reduced-motion:reduce){.gal-slide.activa{animation:none;transform:scale(1.02)}.gal-barra{display:none}.gal-slide{transition:none}}
@media (hover:none){.gal-nav{opacity:1}}
@media (max-width:900px){.tres{grid-template-columns:1fr}}
@media (max-width:1000px){.rejilla.n4{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:760px){
 .bienvenida-esp{height:0}.bienvenida .b-datos{grid-template-columns:1fr;gap:0;border:1px solid var(--borde);border-radius:8px}.bienvenida .b-datos li{flex-direction:row;align-items:baseline;gap:.5rem;border:0;border-radius:0}.bienvenida .b-datos li+li{border-top:1px solid var(--borde)}.bienvenida .b-titulo{font-size:1.45rem}
 .block-container{padding-left:1rem;padding-right:1rem}
 .hero{padding:1rem}.hero .titulo{font-size:1.5rem}
 .rejilla,.rejilla.n2,.rejilla.n4{grid-template-columns:1fr}.tarjeta{min-height:0}
 .kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
 .avisos-grid{grid-template-columns:1fr}.avisos-lateral{grid-template-columns:1fr 1fr}
 .clima{grid-template-columns:1fr}
 .hg-fila{grid-template-columns:1fr 7.4rem;row-gap:.1rem}.hg-nombre{grid-column:1/-1}
 .barra-fila{grid-template-columns:1fr 5.2rem}.barra-id{grid-column:1/-1}.barra-pista{grid-column:1}
}
@media (max-width:520px){.avisos-lateral{grid-template-columns:1fr}}
@media (max-width:760px){
 .pf .pf-titulo{font-size:1.85rem}.pf .pf-sub{font-size:1.02rem}
 .pf-ventajas{grid-template-columns:1fr;gap:.5rem}
 .gal-escena{aspect-ratio:4/3.2;border-radius:12px}
 .gal-nav{width:2.3rem;height:2.3rem;font-size:1.4rem}
 .gal-minis{gap:.3rem}.gal-mini{aspect-ratio:1/1;border-radius:8px}
}
}
"""
st.markdown(f"<style>{ESTILO}</style>", unsafe_allow_html=True)

ESTILO_CLARO = """
:root{--acento:#0c6173;--borde:rgba(32,64,67,.22);--suave:rgba(30,84,87,.07)}
html,body,.stApp{background:#f2f6f3!important;color:#183038!important}
[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#f2f6f3!important;color:#183038!important}
[data-testid="stHeader"]{background:rgba(242,246,243,.92)!important}
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stExpander"],.stApp [data-testid="stCaptionContainer"]{color:#183038}
.stApp [data-testid="stVerticalBlockBorderWrapper"],
.stApp [data-baseweb="select"]>div,.stApp [data-baseweb="input"]>div,
.stApp [data-baseweb="base-input"]{background:#fff!important;color:#183038!important}
.stApp [data-testid="stTextInputRootElement"]{background:#fff!important}
.stApp input,.stApp textarea{color:#183038!important;background:transparent!important}
.stApp input::placeholder{color:#587074!important}
.stApp [data-testid="stDataFrame"],.stApp [data-testid="stExpander"]{background:#fff;border-radius:10px}
.stApp [data-testid="stButton"] button:not([kind="primary"]),
.stApp [data-testid="stDownloadButton"] button{color:#183038;background:#fff;border-color:var(--borde)}
.stApp .pf .pf-eyebrow{color:#0c6173}
.stApp .pf a.pf-boton{color:#fff!important}
.stApp [data-testid="stButtonGroup"] button[role="radio"]{background:rgba(255,255,255,.88)!important}
.stApp [data-testid="stButtonGroup"] button[role="radio"] p{color:#183038!important}
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"]{background:#0c6173!important}
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"] p{color:#fff!important}
.stApp button[kind="primaryFormSubmit"] p{color:#fff!important}
"""


def estilo_bienvenida(claro: bool) -> str:
    """Paisajes del proyecto con transición lenta; el texto queda sobre un panel legible."""
    primero, segundo = fotos.fondos_bienvenida()
    # El degradado conserva el contraste incluso si falta alguna fotografía.
    tinte = "rgba(242,248,244,.42)" if claro else "rgba(7,20,25,.55)"
    panel = "rgba(255,255,255,.91)" if claro else "rgba(12,24,29,.88)"
    letra = "#173039" if claro else "#f6faf8"
    borde = "rgba(26,65,68,.25)" if claro else "rgba(255,255,255,.28)"
    return """
[data-testid="stAppViewContainer"]{position:relative;background:#233d43!important;isolation:isolate}
[data-testid="stAppViewContainer"]::before,[data-testid="stAppViewContainer"]::after{
 content:"";position:fixed;inset:0;pointer-events:none;background-size:cover;background-position:center;
 background-repeat:no-repeat;z-index:0;will-change:opacity,transform}
[data-testid="stAppViewContainer"]::before{background-image:linear-gradient(TINTE,TINTE),FONDO1;
 animation:fondo-viaje 28s ease-in-out infinite alternate}
[data-testid="stAppViewContainer"]::after{background-image:linear-gradient(TINTE,TINTE),FONDO2;
 opacity:0;animation:fondo-cambio 28s ease-in-out infinite}
[data-testid="stMain"]{position:relative;z-index:1;background:transparent!important}
[data-testid="stHeader"]{background:transparent!important}
.st-key-bienvenida_panel{background:PANEL!important;color:LETRA!important;border:1px solid BORDE!important;
 border-radius:18px!important;box-shadow:0 22px 65px rgba(0,0,0,.28);backdrop-filter:blur(12px)}
.st-key-bienvenida_panel [data-testid="stMarkdownContainer"],
.st-key-bienvenida_panel [data-testid="stWidgetLabel"]{color:LETRA!important}
.st-key-bienvenida_panel .b-datos li{background:rgba(128,128,128,.09);border-color:BORDE}
.stApp [data-testid="stButtonGroup"] button[role="radio"]{border-color:BORDE}
SELECTOR_OSCURO
@keyframes fondo-viaje{from{transform:scale(1.02) translateX(0)}to{transform:scale(1.12) translateX(-1.5%)}}
@keyframes fondo-cambio{0%,58%{opacity:0;transform:scale(1.03)}68%,82%{opacity:1;transform:scale(1.12)}95%,100%{opacity:0;transform:scale(1.03)}}
@media (prefers-reduced-motion:reduce){[data-testid="stAppViewContainer"]::before,
 [data-testid="stAppViewContainer"]::after{animation:none!important}
 [data-testid="stAppViewContainer"]::after{display:none}}
@media (max-width:760px){.st-key-bienvenida_panel{backdrop-filter:none}}
""".replace("FONDO1", primero or "linear-gradient(#315b60,#173239)") \
       .replace("FONDO2", segundo or "linear-gradient(#233d43,#173239)") \
       .replace("TINTE", tinte).replace("PANEL", panel).replace("LETRA", letra).replace("BORDE", borde) \
       .replace("SELECTOR_OSCURO", "" if claro else """
.stApp [data-testid="stButtonGroup"] button[role="radio"]{background:rgba(12,24,29,.75)!important}
.stApp [data-testid="stButtonGroup"] button[role="radio"] p{color:#f6faf8!important}
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"]{background:#0f8098!important}
""")


# ------------------------------------------------------------------ datos (cacheados)
@st.cache_data
def datos_base():
    return vr.cargar_catalogo(), vr.cargar_inventario(), vr.cargar_destinos(), vr.cargar_verificacion()


@st.cache_data
def datos_visor(id_ruta: str, fila: dict):
    return vr.datos_visor(id_ruta, fila)


@st.cache_data
def rutas_estudio():
    """Las rutas elegibles con su asignación K-means archivada y contrastada con el catálogo."""
    catalogo = vr.cargar_catalogo()
    destinos = vr.cargar_destinos()
    if not any(f["estado_modelado"] == vr.ELEGIBLE for f in catalogo):
        return []
    k3 = vr.clasificacion_kmeans_k3(catalogo)
    archivo = vr.archivo_clasificacion_dificultad()
    desniveles = {}
    with archivo.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            desniveles[fila["id_ruta"]] = float(fila["desnivel_negativo_total_m"])
    rutas = []
    for fila in catalogo:
        if fila["estado_modelado"] != vr.ELEGIBLE:
            continue
        d = k3[fila["id_ruta"]]
        regla = vr.dificultad_fisica_estimada(fila["id_ruta"], catalogo)
        lugar, destino = vr._destino_de(fila, destinos)
        rutas.append({**fila, "lugar": lugar, "destino_exacto": destino, "nivel": d["nivel"], "orden": d["orden"],
                      "horas": regla["horas_estimadas"], "sensible": d["sensible"],
                      "descenso_m": desniveles.get(fila["id_ruta"], 0.0), "cambios": d["escenarios_cambio"],
                      "cerca_de_frontera": d["cerca_de_frontera"], "nivel_regla": regla["nivel"]})
    return rutas


def humanizar(texto: str, nombres: dict[str, str]) -> str:
    """Los avisos vienen del análisis con identificadores internos; la vista principal usa nombres de ruta."""
    texto = re.sub(r"\s*según I\d+/E\d+", "", texto)
    texto = re.sub(r"\s*Su clase física es relativa a las 20 rutas estudiadas[^.]*\.", "", texto)
    texto = re.sub(r"\bR\d{3}\b", lambda m: "«" + nombres.get(m.group(0), "otra ruta") + "»", texto)
    return (texto.replace("un DEM de 30 m", "un modelo de elevación de 30 m de resolución")
                 .replace("No forma parte del índice de esfuerzo.", "No forma parte de la categoría de dificultad física."))


def num(valor, decimales: int = 2) -> str:
    return vz.numero(valor, decimales)


def tipo_texto(fila) -> str:
    return "Circuito" if fila["tipo_recorrido"] == "circular" else "Ida y vuelta"


def rango_km(lista, nivel) -> str:
    d = [float(r["distancia_total_km"]) for r in lista if r["nivel"] == nivel]
    return f"{vz.numero(min(d), 2)}–{vz.numero(max(d), 2)} km" if d else "—"


def aviso_corto(fila, verificacion) -> str:
    """Texto breve para la tarjeta: solo si hay un aviso de acceso, trazado o alta montaña pendiente de confirmar."""
    filas = [r for r in verificacion if r["clave"] == fila["id_ruta"] and r["tipo"] in ("destacada", "advertencia", "nombre_acceso")]
    if any(r["tipo"] == "destacada" for r in filas):
        return "Alta montaña: revisa los avisos de la ficha."
    if any(r["tipo"] == "nombre_acceso" for r in filas):
        return "Punto de inicio por verificar: revisa la ficha."
    if filas:
        return "Falta confirmar acceso o trazado: revisa la ficha."
    return ""


def tarjeta(fila, verificacion, seleccionada=False) -> str:
    return vz.tarjeta_ruta(fila["nombre_ruta"], fila["lugar"], fila["nivel"], fila["distancia_total_km"], fila["ascenso_total_m"],
                           tipo_texto(fila), aviso_corto(fila, verificacion), seleccionada)


def ir_a_detalle(id_ruta: str):
    """Desde «Comparar alternativas»: cambia de sección y abre la ficha de la ruta."""
    st.session_state["seccion"] = SECCIONES[0]
    abrir_ruta(id_ruta)


def abrir_ruta(id_ruta: str):
    """Abre la ficha (mapa, perfil, avisos y descargas) en lugar de la lista y vuelve al inicio de la página."""
    st.session_state["ruta_detalle"] = id_ruta
    st.session_state["subir_al_inicio"] = True


def volver_a_la_lista():
    st.session_state.pop("ruta_detalle", None)
    st.session_state["subir_al_inicio"] = True


def mostrar_todas():
    st.session_state["mostrar_todas"] = True


def subir_al_inicio():
    """Tras abrir o cerrar una ficha, Streamlit conserva el desplazamiento; aquí se lleva la vista al inicio."""
    if not st.session_state.pop("subir_al_inicio", False):
        return
    guion = ("<script>(function(){var d=window.parent&&window.parent.document?window.parent.document:document;"
             "var m=d.querySelector('[data-testid=\"stMain\"]');if(m)m.scrollTo({top:0});"
             "(window.parent||window).scrollTo({top:0});window.scrollTo({top:0});})();</script>")
    try:
        st.html(guion, unsafe_allow_javascript=True)
    except TypeError:  # versiones de Streamlit sin esa opción: la ficha se abre igual, sin desplazar
        pass


# ================================================================== cabecera
def guardar_alias():
    """Se ejecuta al enviar el formulario de bienvenida (botón o tecla Enter)."""
    alias = vr.limpiar_alias(st.session_state.get("alias_borrador", ""))
    st.session_state["alias_sesion"] = alias
    st.session_state["alias_vacio"] = not alias


def cambiar_alias():
    st.session_state["alias_sesion"] = ""
    st.session_state["alias_vacio"] = False


def mostrar_privacidad():
    """Información visible antes de solicitar el nombre y durante toda la visita."""
    st.markdown(dedent("""
        **Responsable del tratamiento:** Daniel Carranza. Contacto:
        [danycv2022@gmail.com](mailto:danycv2022@gmail.com) · 0984017687.

        **Qué datos usa esta página:** el nombre o apodo que escribes para saludarte,
        la ruta y los filtros que eliges y, si los ingresas, tus límites de distancia y subida.
        La página no solicita tu ubicación GPS, contraseña, documento de identidad ni datos de salud.

        **Para qué y durante cuánto tiempo:** estos datos se usan para mostrar tu visita y tus elecciones.
        El apodo y las preferencias se mantienen en la sesión de Streamlit del servidor; la aplicación
        no crea cuentas ni una base de datos de visitantes. La sesión termina al cerrar o recargar la pestaña,
        aunque una desconexión breve puede conservarla temporalmente. Puedes cambiar el nombre desde la página.
        Si no deseas usar tu nombre real, puedes escribir un apodo.

        **Servicios externos:** la página está alojada en Streamlit Community Cloud, con infraestructura
        en Estados Unidos. Al abrir el mapa, el navegador solicita imágenes a OpenStreetMap o Esri según
        la capa elegida; esos proveedores pueden recibir datos técnicos de la conexión, como la dirección IP.
        Solo si pulsas «Consultar clima de esta ruta», el servidor envía las coordenadas de la ruta a
        Open-Meteo; no envía tu apodo. El alojamiento y esos servicios pueden conservar registros técnicos
        según sus propias políticas.

        **Clasificación:** los niveles de esfuerzo se calculan sobre las rutas, no sobre las personas.
        La página no crea perfiles personales ni decide automáticamente tu aptitud para caminar.

        **Tus derechos:** puedes solicitar acceso, rectificación, eliminación, oposición, limitación o
        portabilidad de tus datos, y presentar un reclamo, escribiendo al correo del responsable.
        También puedes acudir a la [Superintendencia de Protección de Datos Personales](https://www.spdp.gob.ec/).
        Cambiar el apodo modifica el saludo de esta sesión; para retirar el apodo de la sesión actual,
        cierra o recarga la pestaña. Esto no borra los posibles registros técnicos de los proveedores externos.

        Consulta las políticas de [Streamlit](https://streamlit.io/privacy-policy),
        [OpenStreetMap](https://osmfoundation.org/wiki/Privacy_Policy),
        [Esri](https://www.esri.com/en-us/privacy/privacy-statements/privacy-statement) y
        [Open-Meteo](https://open-meteo.com/en/terms) para conocer su tratamiento independiente.
        """).strip())


if st.session_state.get("modo_visual") not in ("Oscuro", "Claro"):
    st.session_state["modo_visual"] = "Oscuro"
with st.container(horizontal=True, horizontal_alignment="right"):
    st.segmented_control("Apariencia", ["Oscuro", "Claro"], key="modo_visual")
modo_claro = st.session_state["modo_visual"] == "Claro"
if modo_claro:
    st.markdown(f"<style>{ESTILO_CLARO}</style>", unsafe_allow_html=True)

st.session_state["alias_sesion"] = vr.limpiar_alias(st.session_state.get("alias_sesion", ""))
if not st.session_state["alias_sesion"]:
    st.markdown(f"<style>{estilo_bienvenida(modo_claro)}</style>", unsafe_allow_html=True)
    st.markdown('<div class="bienvenida-esp"></div>', unsafe_allow_html=True)
    with st.columns([1, 2, 1])[1]:
        with st.container(border=True, key="bienvenida_panel"):
            st.markdown(
                """<div class="bienvenida">
<p class="b-sello">Proyecto de titulación · PUCE</p>
<p class="b-titulo">Rutas de trekking en Pichincha</p>
<p class="b-lema">Consulta qué tan exigente es físicamente cada ruta antes de planificar tu caminata.</p>
<ul class="b-datos">
<li><b>20</b><span>rutas estudiadas</span></li>
<li><b>3</b><span>niveles: Fácil, Moderada, Difícil</span></li>
<li><b>Mapa</b><span>y perfil de altura de cada ruta</span></li>
</ul></div>""",
                unsafe_allow_html=True,
            )
            st.caption("Tu nombre o apodo se usa para saludarte durante esta visita. Lee cómo se tratan tus datos antes de continuar.")
            with st.expander("Privacidad y protección de datos"):
                mostrar_privacidad()
            with st.form("bienvenida", border=False):
                st.text_input("¿Cómo te llamas?", max_chars=40, placeholder="Tu nombre o un apodo", key="alias_borrador")
                st.form_submit_button("Entrar a explorar", key="guardar_alias", type="primary", width="stretch",
                                      on_click=guardar_alias)
            if st.session_state.get("alias_vacio"):
                st.warning("Escribe un nombre con al menos una letra o número para continuar.")
    st.stop()

with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):
    st.markdown(f'<p class="saludo">Hola, {escape(st.session_state["alias_sesion"])}.</p>', unsafe_allow_html=True, width="content")
    st.button("Cambiar nombre", key="cambiar_alias", type="tertiary", on_click=cambiar_alias)

try:
    catalogo, inventario, destinos, verificacion = datos_base()
    rutas = rutas_estudio()
except (OSError, ValueError, KeyError) as error:
    st.error(f"No se pudieron cargar las rutas: {error}")
    st.stop()
nombres = {f["id_ruta"]: f["nombre_ruta"] for f in catalogo}
por_id = {r["id_ruta"]: r for r in rutas}

if not rutas:
    st.warning("No hay alternativas elegibles para mostrar todavía.")
    st.stop()

if st.session_state.get("seccion", SECCIONES[0]) == SECCIONES[0] and not st.session_state.get("ruta_detalle"):
    conteos = {n: sum(1 for r in rutas if r["nivel"] == n) for n in vz.NIVELES}
    st.markdown(f"<style>{fotos.css_fotos()}</style>", unsafe_allow_html=True)
    ventajas = vz.portada_marketing(conteos)
    texto, _, caja = ventajas.partition('<div class="pf-ventajas">')
    st.markdown(texto, unsafe_allow_html=True)
    galeria = vz.galeria_interactiva([fotos.foto_por_id(i) for i in fotos.ORDEN])
    st.html(galeria)
    st.markdown('<div class="pf-ventajas">' + caja, unsafe_allow_html=True)

if st.session_state.get("seccion") not in SECCIONES:
    st.session_state["seccion"] = SECCIONES[0]
seccion = st.segmented_control("Sección", list(SECCIONES), key="seccion", label_visibility="collapsed") or SECCIONES[0]


# ================================================================== ficha de una ruta
def ficha(fila):
    id_ruta = fila["id_ruta"]
    perfil = vr.cargar_perfil(id_ruta)
    acceso = vr.verificar_acceso(fila, (perfil[0]["lat"], perfil[0]["lon"]), verificacion)
    st.subheader(fila["nombre_ruta"])
    st.caption(f"{fila['lugar']} · destino: {fila['destino_exacto']} · {tipo_texto(fila)}")
    st.markdown(vz.insignia_nivel(fila["nivel"], fila["sensible"]), unsafe_allow_html=True)
    st.caption("El nivel de esfuerzo es orientativo: compara la distancia y la subida de las rutas de esta página. "
               "Revisa también el terreno, el acceso y el clima antes de salir.")
    if fila["sensible"]:
        st.caption("Este nivel puede variar si se revisan las medidas de la ruta.")
    elif fila["cerca_de_frontera"]:
        st.caption("El esfuerzo de esta ruta se parece al de rutas de otro nivel.")
    for texto_destacado in vr.advertencias_destacadas(id_ruta, verificacion):
        st.warning(humanizar(texto_destacado, nombres))

    try:
        visor_html = vr.construir_visor_html(datos_visor(id_ruta, fila))
    except (OSError, ValueError, KeyError) as error:
        st.error(f"No se puede representar esta ruta: {error}")
        return
    st.iframe(visor_html, height=800, alt=f"Mapa interactivo y perfil de elevación de {fila['nombre_ruta']}")
    if fila["tipo_recorrido"] != "circular":
        st.caption("En el mapa se dibuja la ida; la distancia, la subida y la bajada incluyen el regreso por el mismo camino. "
                   "La simulación es una animación visual, no una grabación GPS ni navegación en tiempo real.")
    else:
        st.caption("La simulación es una animación visual del circuito, no una grabación GPS ni navegación en tiempo real.")

    st.markdown(vz.teselas([
        ("distancia", num(fila["distancia_total_km"]), "km", "Distancia total"),
        ("subida", num(fila["ascenso_total_m"], 0), "m", "Subida acumulada"),
        ("bajada", num(fila["descenso_m"], 0), "m", "Bajada acumulada"),
        ("altitud", num(fila["elevacion_max_m"], 0), "m", "Altitud máxima"),
    ]), unsafe_allow_html=True)

    st.markdown("#### Avisos de esta ruta")
    st.caption("Son independientes de la categoría: una ruta Fácil puede tener altitud, acceso restringido o terreno exigente.")
    if acceso["nota"]:
        st.warning(humanizar(acceso["nota"], nombres))
    separados = vr.avisos_separados(id_ruta, fila, inventario, verificacion)
    st.markdown(vz.avisos_ruta(
        [humanizar(aviso, nombres) for aviso in separados["altitud"]],
        [humanizar(aviso, nombres) for aviso in separados["acceso"]],
        [humanizar(aviso, nombres) for aviso in separados["caracter_tecnico"]],
    ), unsafe_allow_html=True)
    if separados["otros"]:
        st.markdown("**Otros avisos de verificación**")
        for aviso in separados["otros"]:
            st.markdown(f"- {humanizar(aviso, nombres)}")

    st.markdown("#### Descargas")
    d = st.columns(2)
    d[0].download_button("Descargar datos del mapa (GeoJSON)", data=vr.ruta_trazado(id_ruta).read_bytes(),
                         file_name=f"{id_ruta}_trazado.geojson", mime="application/geo+json", width="stretch")
    d[1].download_button("Descargar ruta para GPS (GPX)",
                         data=vr.gpx_ida(id_ruta, fila["nombre_ruta"]),
                         file_name=f"{id_ruta}_trazado.gpx", mime="application/gpx+xml", width="stretch")
    st.caption("El archivo GPX muestra el camino de ida. Procede de OpenStreetMap y no es una grabación hecha sobre el terreno.")

    with st.expander("¿Qué significa este nivel?"):
        st.markdown(
            f"Esta ruta tiene **{num(fila['distancia_total_km'])} km** en total y acumula "
            f"**{num(fila['ascenso_total_m'], 0)} m de subida**. Al compararla con las otras rutas de la página, "
            f"su nivel de esfuerzo es **{fila['nivel']}**. Este nivel te ayuda a comparar caminatas; "
            "no indica cómo está el sendero ni si es adecuado para ti."
        )
        if fila["sensible"]:
            st.caption("Las medidas de subida y pendiente proceden de mapas de elevación y pueden cambiar al revisarse. "
                       "Por eso este nivel podría variar.")

    with st.expander("Clima estimado cerca del recorrido (opcional)"):
        st.caption(
            "Consulta el tiempo aproximado en el inicio y la llegada (o el punto más alto, si la ruta es circular). "
            "No es una medición hecha en el sendero. El tiempo puede cambiar rápido en montaña: comprueba los avisos oficiales antes de salir."
        )
        if st.button("Consultar clima de esta ruta", key=f"consultar_clima_{id_ruta}"):
            try:
                st.session_state[f"clima_{id_ruta}"] = {
                    "consultado": time.time(),
                    "puntos": clima.consultar(vr.cargar_perfil(id_ruta), circular=fila["tipo_recorrido"] == "circular"),
                }
            except (clima.ClimaNoDisponible, ValueError, OSError):
                st.session_state.pop(f"clima_{id_ruta}", None)
                st.warning("El servicio meteorológico no respondió. El mapa y los datos de la ruta siguen disponibles.")
    consulta = st.session_state.get(f"clima_{id_ruta}")
    if consulta and time.time() - consulta["consultado"] > 900:
        st.session_state.pop(f"clima_{id_ruta}", None)
        consulta = None
        st.info("La consulta anterior ya tiene más de 15 minutos. Vuelve a consultar para ver datos recientes.")
    if consulta:
        st.markdown(vz.panel_clima(perfil, consulta["puntos"]), unsafe_allow_html=True)
        st.caption(
            "Fuente: Open-Meteo (CC BY 4.0). Son estimaciones recientes, no mediciones en el sendero. "
            "La hora indica cuándo corresponden los datos; la lluvia se refiere al periodo reciente. "
            "Verifica pronósticos y avisos oficiales antes de caminar."
        )

    ficha_inv = inventario.get(id_ruta, {})
    id_fuente = str(ficha_inv.get("identificador_fuente", "—"))
    if len(id_fuente) > 90:
        id_fuente = id_fuente[:60].replace("|", " | ") + f"… ({len(id_fuente.split('|'))} segmentos en total)"
    dem, filtrado = vr.fuente_elevacion(id_ruta)
    with st.expander("Datos técnicos, fuentes y licencias"):
        st.markdown(
            f"- **Inclinación:** media {num(fila['pendiente_media_abs_pct'], 1)} %; el 5 % de los tramos más empinados supera "
            f"{num(fila['pendiente_p95_abs_pct'], 1)} %\n"
            f"- **Altitud:** de {num(fila['elevacion_min_m'], 0)} a {num(fila['elevacion_max_m'], 0)} m\n"
            f"- **Trazado:** {ficha_inv.get('fuente_trazado', '—')} · {id_fuente} · "
            f"consultado el {ficha_inv.get('fecha_consulta', '—')}\n"
            f"- **Enlace de la fuente:** {ficha_inv.get('url_fuente', '—')}\n"
            f"- **Licencia del trazado:** {ficha_inv.get('licencia_nombre', '—')} ({ficha_inv.get('licencia_url', '—')})\n"
            f"- **Elevación:** {dem}\n"
            f"- **Filtrado del perfil:** {filtrado}\n"
            f"- **Calidad preliminar:** {ficha_inv.get('calidad_preliminar', '—')} · decisión: {ficha_inv.get('decision', '—')}\n"
            f"- **Compatibilidad con trekking no técnico:** {ficha_inv.get('motivo_compatibilidad', '—')}"
        )
        originales = vr.advertencias(id_ruta, verificacion)
        if originales:
            st.markdown("**Texto original de los avisos (con identificadores internos)**")
            for aviso in originales:
                st.markdown(f"- {aviso}")


# ================================================================== sección: explorar rutas
INICIALES = 12


def detalle(id_ruta: str):
    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    c1.button("Volver a la lista", key="volver_lista", icon=":material/arrow_back:", on_click=volver_a_la_lista, width="stretch")
    ids = [r["id_ruta"] for r in sorted(rutas, key=lambda r: (r["orden"], r["horas"], r["nombre_ruta"]))]
    c2.selectbox("Cambiar de ruta", ids, key="ruta_detalle", format_func=lambda i: f"{por_id[i]['nombre_ruta']} · {por_id[i]['nivel']}")
    ficha(por_id[st.session_state["ruta_detalle"]])


def explorar():
    if st.session_state.get("ruta_detalle") in por_id:
        detalle(st.session_state["ruta_detalle"])
        return
    st.session_state.pop("ruta_detalle", None)
    st.markdown("#### Elige una ruta")
    lugares_lista = sorted({r["lugar"] for r in rutas})
    c1, c2, c3 = st.columns([1.1, 1.3, 1])
    filtro_lugar = c1.selectbox("Lugar", [TODOS] + lugares_lista, key="filtro_lugar")
    filtro_nombre = c2.text_input("Buscar por nombre", key="filtro_nombre", placeholder="Por ejemplo: cascada, mirador, sendero")
    filtro_nivel = c3.selectbox("Nivel de esfuerzo", [TODOS] + list(vz.NIVELES), key="filtro_nivel")
    consulta = (filtro_nombre or "").strip().lower()
    lista = [r for r in rutas
             if (filtro_lugar == TODOS or r["lugar"] == filtro_lugar)
             and (filtro_nivel == TODOS or r["nivel"] == filtro_nivel)
             and (not consulta or consulta in r["nombre_ruta"].lower() or consulta in r["lugar"].lower()
                  or consulta in r["destino_exacto"].lower())]
    lista.sort(key=lambda r: (r["orden"], r["horas"], r["nombre_ruta"]))
    if not lista:
        st.info("Ninguna ruta coincide con estos filtros. Prueba con otro lugar, otro nombre o «Todos» en dificultad.")
        return
    filtrado = filtro_lugar != TODOS or filtro_nivel != TODOS or bool(consulta)
    visibles = lista if (filtrado or st.session_state.get("mostrar_todas")) else lista[:INICIALES]
    st.markdown("**Niveles de esfuerzo:** Fácil, Moderada y Difícil te ayudan a comparar las rutas según "
                "su distancia y subida. Mira los avisos de cada sendero antes de elegir.")
    st.caption(f"{len(visibles)} de {len(rutas)} rutas. El orden facilita la exploración; la primera no necesariamente es la mejor para ti. "
               "Pulsa «Ver ruta» para abrir el mapa, el perfil y los avisos.")
    for inicio in range(0, len(visibles), 4):
        columnas = st.columns(4)
        for columna, r in zip(columnas, visibles[inicio:inicio + 4]):
            with columna:
                st.markdown(tarjeta(r, verificacion).replace('class="tarjeta"', 'class="tarjeta fija"'), unsafe_allow_html=True)
                st.button("Ver ruta", key=f"ver_{r['id_ruta']}", on_click=abrir_ruta, args=(r["id_ruta"],), width="stretch",
                          help=f"Mapa, perfil, avisos y descargas de {r['nombre_ruta']}")
    if len(visibles) < len(lista):
        st.button(f"Mostrar las {len(lista) - len(visibles)} rutas restantes", key="mostrar_todas_btn", on_click=mostrar_todas,
                  icon=":material/expand_more:", width="stretch")


# ================================================================== sección: comparar alternativas
def comparar():
    st.markdown("#### Comparar alternativas al mismo destino")
    st.write("Solo se comparan rutas que llegan al mismo destino exacto. Cumbres, miradores o cascadas cercanos no se mezclan para fabricar opciones.")
    grupos = {}
    for r in rutas:
        grupos.setdefault((r["lugar"], r["destino_exacto"]), []).append(r)
    varios = {f"{d} · {l} · {len(v)} alternativas": v for (l, d), v in sorted(grupos.items()) if len(v) > 1}
    unicos = len(grupos) - len(varios)
    if not varios:
        st.info("Ahora mismo ningún destino tiene más de una alternativa elegible.")
        return
    etiqueta = st.selectbox("Destino con varias alternativas", list(varios), key="destino_comparar")
    st.caption(f"Hay {len(varios)} destinos con varias alternativas. Los otros {unicos} destinos tienen una sola ruta elegible y, por eso, no tienen comparación.")
    alternativas = [dict(r) for r in varios[etiqueta]]
    vr.validar_comparacion(alternativas)
    alternativas.sort(key=lambda r: (r["horas"], r["nombre_ruta"]))
    st.markdown(vz.rejilla([tarjeta(r, verificacion) for r in alternativas], columnas=min(3, len(alternativas))), unsafe_allow_html=True)
    st.caption("Compara las opciones que llegan al mismo lugar. El nivel resume el esfuerzo de la caminata; revisa también el acceso, el estado del sendero "
               "y tu condición física.")
    barras = [dict(r, etiqueta=r["nombre_ruta"]) for r in alternativas]
    b1, b2 = st.columns(2)
    b1.markdown(vz.barras_relativas(barras, "distancia_total_km", "Distancia total", "km", 1), unsafe_allow_html=True)
    b2.markdown(vz.barras_relativas(barras, "ascenso_total_m", "Subida acumulada", "m", 0), unsafe_allow_html=True)
    tabla = [
        {
            "Ruta": r["nombre_ruta"],
            "Nivel de esfuerzo": r["nivel"] + (" (puede variar)" if r["sensible"] else ""),
            "Distancia total (km)": round(float(r["distancia_total_km"]), 2),
            "Subida (m)": round(float(r["ascenso_total_m"])),
            "Bajada (m)": round(float(r["descenso_m"])),
            "Altitud máx. (m)": round(float(r["elevacion_max_m"])),
            "Tipo": tipo_texto(r),
            "Destino exacto": r["destino_exacto"],
        }
        for r in alternativas
    ]
    st.dataframe(tabla, hide_index=True, width="stretch")
    st.caption("«Puede variar» indica que el nivel podría cambiar al revisar las medidas de la ruta.")
    st.markdown("**Ver una alternativa en detalle**")
    columnas = st.columns(len(alternativas))
    for columna, r in zip(columnas, alternativas):
        columna.button(f"Abrir: {r['nombre_ruta']}", key=f"abrir_{r['id_ruta']}", on_click=ir_a_detalle, args=(r["id_ruta"],), width="stretch")
    with st.expander("Filtrar por mis límites de distancia o subida"):
        st.caption("Indica límites personales opcionales. Es un filtro informativo, no una evaluación de seguridad o aptitud.")
        clave = f"{alternativas[0]['lugar']}_{alternativas[0]['destino_exacto']}"
        controles = st.columns(2)
        distancia_preferida = controles[0].number_input(
            "Distancia total máxima (km)", min_value=0.0, value=0.0, step=0.5,
            key=f"limite_distancia_{clave}", help="0 = sin límite; incluye la ida y el regreso.")
        ascenso_preferido = controles[1].number_input(
            "Subida máxima (m)", min_value=0.0, value=0.0, step=50.0,
            key=f"limite_ascenso_{clave}", help="0 = sin límite; la subida es aproximada.")
        distancia_preferida = float(distancia_preferida or 0)
        ascenso_preferido = float(ascenso_preferido or 0)
        if distancia_preferida or ascenso_preferido:
            coincidencias = vr.coincidencias_limites(alternativas, distancia_max_km=distancia_preferida or None,
                                                     ascenso_max_m=ascenso_preferido or None)
            coinciden = [nombres[c["id_ruta"]] for c in coincidencias if c["coincide"]]
            if coinciden:
                st.success("Coinciden con tus límites: " + ", ".join(coinciden) + ". Las demás siguen visibles arriba.")
            else:
                st.info("Ninguna alternativa de este destino coincide con ambos límites. Puedes ampliar los valores o explorar otro destino.")
            st.caption("Esto no indica cuál ruta es mejor: revisa el mapa, el acceso, el clima y las condiciones oficiales.")


# ================================================================== sección: explicación para visitantes
def metodologia():
    conteos = {n: sum(1 for r in rutas if r["nivel"] == n) for n in vz.NIVELES}
    st.markdown("#### Encuentra una caminata a tu ritmo")
    st.write("Explora el mapa, compara la distancia y la subida, y revisa los avisos de cada ruta antes de elegir.")
    st.markdown(vz.resumen_niveles(conteos), unsafe_allow_html=True)
    st.caption("Los niveles sirven para comparar las 20 rutas incluidas aquí; no abarcan todos los senderos de Pichincha.")

    st.markdown("#### ¿Qué tiene en cuenta el nivel?")
    st.write("La distancia total que caminarías y la subida acumulada del recorrido. En una ruta de ida y vuelta, "
             "la distancia incluye el regreso; en un circuito se considera la vuelta completa.")
    st.markdown(vz.flujo([
        ("Explora", "Elige un lugar o busca una cascada, un mirador o un sendero."),
        ("Compara", "Mira cuánto caminarías y cuánto subirías; si hay varias rutas al mismo destino, verás sus opciones juntas."),
        ("Revisa", "Abre el mapa y consulta los avisos de acceso, terreno, altitud y clima."),
    ]), unsafe_allow_html=True)

    with st.expander("¿Qué significan Fácil, Moderada y Difícil?"):
        st.markdown(
            "- **Fácil:** menor esfuerzo al comparar estas rutas por distancia y subida.\n"
            "- **Moderada:** esfuerzo intermedio entre las rutas de la página.\n"
            "- **Difícil:** mayor esfuerzo dentro de esta selección.\n"
            "\nEl nivel habla del esfuerzo de caminar, no de obstáculos, experiencia necesaria o seguridad. "
            "Incluso una ruta Fácil puede tener tramos exigentes o acceso restringido."
        )
        st.markdown(vz.tabla_html(
            ["Nivel", "Rutas", "Distancia total"],
            [[escape(n), str(conteos[n]), rango_km(rutas, n)] for n in vz.NIVELES]), unsafe_allow_html=True)

    with st.expander("Antes de salir"):
        st.markdown(
            "- Consulta si el sendero está abierto y si requiere entrada o permiso.\n"
            "- Revisa el clima y lleva equipo adecuado para el terreno y la altitud.\n"
            "- Valora tu experiencia y condición física. El nivel no sustituye tu criterio ni las indicaciones del lugar."
        )
    sensibles = [r for r in rutas if r["sensible"]]
    with st.expander("¿Por qué algunas rutas dicen «puede variar»?"):
        st.write("La subida y la pendiente se estiman con mapas de altura. Si esas medidas se revisan, algunas rutas "
                 "podrían cambiar de nivel. En cada ficha marcamos los casos que necesitan más cautela.")
        st.markdown("**Rutas con esa indicación:** " + ", ".join(sorted(r["nombre_ruta"] for r in sensibles)) + ".")


subir_al_inicio()
if seccion == SECCIONES[0]:
    explorar()
elif seccion == SECCIONES[1]:
    comparar()
else:
    metodologia()

st.divider()
with st.expander("Privacidad y protección de datos"):
    mostrar_privacidad()
st.caption(
    "Datos del trazado © colaboradores de OpenStreetMap (ODbL 1.0) · Elevación: Copernicus DEM GLO-30 (Unión Europea/ESA) · "
    "Mapas base: © OpenStreetMap contributors e imágenes satelitales © Esri, Maxar y Earthstar Geographics · Visor: Leaflet (BSD-2). "
    "Consulta acceso, clima y condiciones oficiales antes de salir; esta página no evalúa seguridad ni aptitud personal."
)
