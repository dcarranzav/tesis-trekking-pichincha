"""Rutas de trekking en Pichincha: dificultad física estimada de 20 recorridos.

Ejecutar con `streamlit run app.py`. No usa base de datos ni cuentas: la bienvenida pide un nombre solo para
saludar, y ese nombre vive en la memoria de la sesión del navegador. La categoría Fácil/Moderada/Difícil
viene de `vista_rutas.dificultad_fisica_estimada()` (regla archivada en 07_resultados/tablas); esta página
no calcula umbrales ni crea otro puntaje. No recomienda salidas ni evalúa seguridad, acceso, técnica ni clima.

Secciones: «Explorar rutas» (filtros, tarjetas y ficha con mapa), «Comparar alternativas» (solo rutas que llegan
al mismo destino exacto) y «Metodología y límites». K-means, DBSCAN y el índice HEN se mencionan únicamente
como contrastes en el detalle metodológico.
"""

from __future__ import annotations

import csv
import re
import sys
import time
from html import escape
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "06_scripts"))
import vista_rutas as vr  # noqa: E402
import visuales_pagina as vz  # noqa: E402
import fotos_pagina as fotos  # noqa: E402
import clima_rutas as clima  # noqa: E402

SECCIONES = ("Explorar rutas", "Comparar alternativas", "Metodología y límites")
TODOS = "Todos"
ESCENARIOS = {
    "piso_desfavorable_3_kmh": "caminar a 3 km/h en horizontal (terreno más lento)",
    "piso_favorable_5_kmh": "caminar a 5 km/h en horizontal (terreno más rápido)",
    "dem_crudo": "usar las subidas y bajadas sin filtrar el ruido del modelo de elevación",
    "dem_mediana5": "filtrar el ruido del modelo de elevación con una ventana más amplia",
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


# ------------------------------------------------------------------ datos (cacheados)
@st.cache_data
def datos_base():
    return vr.cargar_catalogo(), vr.cargar_inventario(), vr.cargar_destinos(), vr.cargar_verificacion()


@st.cache_data
def datos_visor(id_ruta: str, fila: dict):
    return vr.datos_visor(id_ruta, fila)


@st.cache_data
def rutas_estudio():
    """Las 20 rutas elegibles con su categoría archivada. No se recalcula nada: se lee y se enlaza al catálogo."""
    catalogo = vr.cargar_catalogo()
    destinos = vr.cargar_destinos()
    archivo = vr.archivo_clasificacion_dificultad()
    desniveles = {}
    with archivo.open(encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            desniveles[fila["id_ruta"]] = float(fila["desnivel_negativo_total_m"])
    cambios = {}
    sens = archivo.with_name(archivo.name.replace("clasificacion_dificultad_fisica_", "clasificacion_dificultad_fisica_sensibilidad_"))
    if sens.exists():
        with sens.open(encoding="utf-8-sig", newline="") as f:
            for fila in csv.DictReader(f):
                if fila["cambia_frente_base"] == "si":
                    cambios.setdefault(fila["id_ruta"], []).append((fila["escenario"], fila["nivel"]))
    rutas = []
    for fila in catalogo:
        if fila["estado_modelado"] != vr.ELEGIBLE:
            continue
        d = vr.dificultad_fisica_estimada(fila["id_ruta"], catalogo)
        lugar, destino = vr._destino_de(fila, destinos)
        rutas.append({**fila, "lugar": lugar, "destino_exacto": destino, "nivel": d["nivel"], "orden": d["orden"],
                      "horas": d["horas_estimadas"], "sensible": d["sensible"],
                      "descenso_m": desniveles.get(fila["id_ruta"], 0.0), "cambios": cambios.get(fila["id_ruta"], [])})
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


st.session_state["alias_sesion"] = vr.limpiar_alias(st.session_state.get("alias_sesion", ""))
if not st.session_state["alias_sesion"]:
    st.markdown('<div class="bienvenida-esp"></div>', unsafe_allow_html=True)
    with st.columns([1, 2, 1])[1]:
        with st.container(border=True):
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

st.session_state.setdefault("seccion", SECCIONES[0])
seccion = st.segmented_control("Sección", list(SECCIONES), key="seccion", label_visibility="collapsed") or SECCIONES[0]


# ================================================================== ficha de una ruta
def ficha(fila):
    id_ruta = fila["id_ruta"]
    perfil = vr.cargar_perfil(id_ruta)
    acceso = vr.verificar_acceso(fila, (perfil[0]["lat"], perfil[0]["lon"]), verificacion)
    st.subheader(fila["nombre_ruta"])
    st.caption(f"{fila['lugar']} · destino: {fila['destino_exacto']} · {tipo_texto(fila)}")
    st.markdown(vz.insignia_nivel(fila["nivel"], fila["sensible"]), unsafe_allow_html=True)
    st.caption("Describe solo el esfuerzo físico estimado del recorrido completo. No mide dificultad técnica, acceso, clima, seguridad "
               "ni aptitud personal.")
    if fila["sensible"]:
        st.caption("La categoría cambia en algunos escenarios metodológicos. Más detalle en «Cómo se obtuvo esta categoría», abajo.")
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

    st.markdown("**Dónde cae esta ruta en la escala de esfuerzo estimado**")
    st.markdown(vz.escala_esfuerzo(fila["horas"], fila["nivel"]), unsafe_allow_html=True)
    st.caption(f"Esfuerzo estimado de {num(fila['horas'], 2)} horas de marcha equivalentes. Es un valor de la regla de clasificación, no "
               "una duración garantizada: depende del ritmo, la carga y el estado del sendero.")

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
    d[0].download_button("Descargar trazado (GeoJSON)", data=vr.ruta_trazado(id_ruta).read_bytes(),
                         file_name=f"{id_ruta}_trazado.geojson", mime="application/geo+json", width="stretch")
    d[1].download_button("Descargar trazado de ida (GPX, sin elevaciones ni tiempos)",
                         data=vr.gpx_ida(id_ruta, fila["nombre_ruta"]),
                         file_name=f"{id_ruta}_trazado.gpx", mime="application/gpx+xml", width="stretch")
    st.caption("El GPX es un formato de intercambio derivado del trazado de OpenStreetMap: no es una grabación GPS de campo.")

    with st.expander("Cómo se obtuvo esta categoría"):
        st.markdown(
            f"Para el recorrido completo ({num(fila['distancia_total_km'])} km, {num(fila['ascenso_total_m'], 0)} m de subida y "
            f"{num(fila['descenso_m'], 0)} m de bajada) la regla estima {num(fila['horas'], 2)} horas de esfuerzo. "
            f"Eso corresponde a la categoría **{fila['nivel']}**: Fácil hasta 1 h, Moderada de más de 1 h a 3 h y Difícil por encima de 3 h."
        )
        if fila["sensible"]:
            st.markdown("**Esta ruta es sensible a los supuestos.** Si se cambia alguno de los siguientes, la categoría sería otra:")
            for escenario, nivel in fila["cambios"]:
                st.markdown(f"- {'; '.join(ESCENARIOS.get(e, e) for e in escenario.split('|'))}: {nivel}.")
            st.caption("La categoría publicada es la del escenario base (4 km/h y filtro de elevación de tres puntos). "
                       "Ningún escenario es más verdadero que otro: no hay medidas de campo con las que contrastarlos.")
        else:
            st.caption("La categoría no cambió en ninguno de los escenarios probados (3 y 5 km/h; elevación filtrada con ventanas de tres y cinco puntos, o sin filtrar).")

    with st.expander("Clima estimado cerca del recorrido (opcional)"):
        st.caption(
            "Estimación de un modelo meteorológico externo para el inicio y la llegada (o el punto más alto, en circuitos). "
            "No es una medición en el sendero ni describe cada tramo; puede cambiar rápido en montaña. "
            "No interviene en la categoría de dificultad y no sirve por sí sola para decidir si es seguro salir."
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
            "Fuente: Open-Meteo (CC BY 4.0), valores actuales derivados de modelos. La temperatura, la precipitación y el viento son "
            "variables distintas: pueden coincidir, por ejemplo, una temperatura templada con lluvia. La precipitación corresponde al "
            "último intervalo del modelo (normalmente de unos 15 minutos) y la hora indicada es la validez del dato. "
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
    filtro_nivel = c3.selectbox("Dificultad física estimada", [TODOS] + list(vz.NIVELES), key="filtro_nivel")
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
    st.markdown("**Dificultad física estimada:** Fácil (hasta 1 h de esfuerzo estimado) · Moderada (más de 1 h y hasta 3 h) · "
                "Difícil (más de 3 h).")
    st.caption(f"{len(visibles)} de {len(rutas)} rutas. Ordenadas de menor a mayor esfuerzo físico estimado; el orden no indica cuál elegir. "
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
    st.caption("Ordenadas de menor a mayor esfuerzo físico estimado. Esto no indica cuál elegir: no se evalúan el acceso, el estado del sendero "
               "ni tu condición física.")
    barras = [dict(r, etiqueta=r["nombre_ruta"]) for r in alternativas]
    b1, b2 = st.columns(2)
    b1.markdown(vz.barras_relativas(barras, "distancia_total_km", "Distancia total", "km", 1), unsafe_allow_html=True)
    b2.markdown(vz.barras_relativas(barras, "ascenso_total_m", "Subida acumulada", "m", 0), unsafe_allow_html=True)
    tabla = [
        {
            "Ruta": r["nombre_ruta"],
            "Dificultad física estimada": r["nivel"] + (" (sensible)" if r["sensible"] else ""),
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
    st.caption("«Sensible» indica que la categoría cambia en algunos escenarios metodológicos.")
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
            key=f"limite_ascenso_{clave}", help="0 = sin límite; es una estimación del modelo de elevación.")
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


# ================================================================== sección: metodología y límites
def metodologia():
    conteos = {n: sum(1 for r in rutas if r["nivel"] == n) for n in vz.NIVELES}
    st.markdown("#### El resultado en una mirada")
    st.markdown(vz.resumen_niveles(conteos), unsafe_allow_html=True)
    st.caption("Cada ruta tiene una sola categoría de dificultad física estimada. Las 20 rutas son una muestra intencional, no todas las rutas de Pichincha.")
    st.markdown(vz.grafico_horas([{"nombre": r["nombre_ruta"], "horas": r["horas"], "nivel": r["nivel"], "sensible": r["sensible"]} for r in rutas]),
                unsafe_allow_html=True)

    st.markdown("#### Cómo se calculó")
    st.markdown(vz.flujo([
        ("Reunir trazados", "Recorridos de OpenStreetMap con fuente, licencia y fecha registradas; cada uno se revisó antes de incluirlo."),
        ("Medir", "Distancia, subida y bajada de cada ruta completa (ida y vuelta, o circuito) con la misma fórmula."),
        ("Estimar el esfuerzo", "Se estiman las horas de esfuerzo según la distancia horizontal y el desnivel."),
        ("Categorizar", "Hasta 1 h es Fácil, más de 1 h hasta 3 h es Moderada y más de 3 h es Difícil."),
        ("Probar la sensibilidad", "Se repite con otros ritmos y otros filtros de elevación para ver qué rutas cambian."),
    ]), unsafe_allow_html=True)
    st.markdown(
        "La regla se inspira en el componente de cantidad de esfuerzo del método MIDE, pero **no es el método MIDE completo**: "
        "el proyecto no tiene una valoración homogénea del firme, la orientación ni la severidad del medio de las 20 rutas."
    )
    with st.expander("La regla de esfuerzo, con detalle"):
        st.markdown(
            "- **Componente horizontal:** distancia total ÷ 4 km/h.\n"
            "- **Componente de desnivel:** subida ÷ 400 m/h + bajada ÷ 600 m/h.\n"
            "- **Esfuerzo estimado:** el mayor de los dos componentes más la mitad del menor.\n"
            "- En rutas de ida y vuelta, la bajada del regreso es la subida de la ida y viceversa; en circuitos se usa el perfil completo.\n"
            "- Las elevaciones salen del modelo digital Copernicus DEM GLO-30 (celdas de 30 m), filtradas con la mediana de tres puntos."
        )
        st.markdown(vz.tabla_html(
            ["Categoría", "Esfuerzo estimado", "Rutas", "Distancia"],
            [[escape(n), c, str(conteos[n]), rango_km(rutas, n)]
             for n, c in zip(vz.NIVELES, ("hasta 1 h", "más de 1 h y hasta 3 h", "más de 3 h"))]), unsafe_allow_html=True)
    with st.expander("Qué significa cada categoría, y qué no"):
        st.markdown(
            "- **Fácil, Moderada y Difícil** describen únicamente el **esfuerzo físico estimado** del recorrido completo.\n"
            "- **No** describen dificultad técnica, orientación, estado del sendero, acceso vigente, clima, seguridad ni aptitud personal.\n"
            "- La altitud, el acceso y el carácter técnico se muestran aparte, como avisos de cada ruta."
        )
    sensibles = [r for r in rutas if r["sensible"]]
    with st.expander(f"Sensibilidad: {len(sensibles)} rutas cambian de categoría en algún escenario"):
        st.write("Se repitió la clasificación con 3 y 5 km/h en horizontal y con la elevación filtrada con otra ventana o sin filtrar. "
                 "Las rutas de la tabla cambian al menos en un escenario; la categoría publicada es la del escenario base.")
        filas = []
        for r in sorted(sensibles, key=lambda r: r["nombre_ruta"]):
            texto = "; ".join(f"{' y '.join(ESCENARIOS.get(e, e) for e in esc.split('|'))}: {nivel}" for esc, nivel in r["cambios"])
            filas.append([escape(r["nombre_ruta"]), escape(r["nivel"]), escape(texto)])
        st.markdown(vz.tabla_html(["Ruta", "Categoría publicada", "Escenarios en que cambia"], filas), unsafe_allow_html=True)
    with st.expander("Contrastes metodológicos (para quien revisa la tesis)"):
        st.markdown(
            "- **K-means (dos grupos)** sobre distancia y subida muestra la estructura de la muestra, pero no produce las tres categorías públicas.\n"
            "- **Ward y DBSCAN** se usaron como contraste de esa estructura. DBSCAN deja varias rutas de mayor subida sin grupo y no confirma la clasificación.\n"
            "- **Índice de esfuerzo de referencia (distancia ÷ 5 + subida ÷ 600)** es un antecedente descriptivo; no compite con la categoría.\n"
            "- Ninguno de estos análisis se usa como etiqueta pública ni como recomendación."
        )


subir_al_inicio()
if seccion == SECCIONES[0]:
    explorar()
elif seccion == SECCIONES[1]:
    comparar()
else:
    metodologia()

st.divider()
st.caption(
    "Datos del trazado © colaboradores de OpenStreetMap (ODbL 1.0) · Elevación: Copernicus DEM GLO-30 (Unión Europea/ESA) · "
    "Mapas base: © OpenStreetMap contributors e imágenes satelitales © Esri, Maxar y Earthstar Geographics · Visor: Leaflet (BSD-2). "
    "Consulta acceso, clima y condiciones oficiales antes de salir; esta página no evalúa seguridad ni aptitud personal."
)
