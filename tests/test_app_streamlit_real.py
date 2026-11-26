"""Ejecuta app.py con el Streamlit REAL (streamlit.testing.v1.AppTest).

Se omite si Streamlit no está instalado. A diferencia de test_app_humo.py, usa la API real:
valida firmas (st.iframe, st.segmented_control, st.button con on_click, st.download_button...), filtros,
cambio de sección y apertura de una alternativa desde la comparación.
Las secciones se cambian escribiendo en `at.session_state["seccion"]`, que funciona con cualquier widget con clave.
"""

import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from streamlit.testing.v1 import AppTest
except ImportError:  # pragma: no cover
    AppTest = None

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "06_scripts"))
CODIGO_RUTA = re.compile(r"\bR\d{3}\b")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅]")
OTROS = re.compile(r"k-means|dbscan|ward|mide|centroide|estandariz|índice de esfuerzo", re.I)


def nueva(seccion=None, registrado=True, **estado):
    at = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=90)
    if registrado:
        at.session_state["alias_sesion"] = "Usuario de prueba"
    if seccion:
        at.session_state["seccion"] = seccion
    for clave, valor in estado.items():
        at.session_state[clave] = valor
    return at.run()


def texto(at):
    partes = [e.value for e in at.markdown if not str(e.value).startswith("<style>")] + [e.value for e in at.caption]
    partes += [e.value for e in at.info] + [e.value for e in at.warning] + [e.value for e in at.subheader]
    partes += [m.label for m in at.metric]
    return "\n".join(str(p) for p in partes)


def visible(at):
    """Texto de la vista principal: sin el contenido de los desplegables técnicos."""
    return re.sub(r"<[^>]+>", " ", texto(at))


@unittest.skipIf(AppTest is None, "Streamlit no está instalado en este entorno")
class AppStreamlitReal(unittest.TestCase):
    def test_el_modo_claro_funciona_en_bienvenida_y_en_la_pagina(self):
        entrada = nueva(registrado=False, modo_visual="Claro")
        self.assertFalse(entrada.exception, [e.value for e in entrada.exception])
        self.assertEqual(entrada.session_state["modo_visual"], "Claro")
        self.assertIn("fondo-cambio", "".join(str(e.value) for e in entrada.markdown))
        pagina = nueva(modo_visual="Claro")
        self.assertFalse(pagina.exception, [e.value for e in pagina.exception])
        self.assertIn("#e2f2f1", "".join(str(e.value) for e in pagina.markdown))

    def test_arranque_sin_excepciones_con_portada_sin_aviso_de_desarrollo(self):
        at = nueva()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        t = texto(at)
        self.assertIn("Niveles de esfuerzo", t)
        self.assertNotIn("Versión en desarrollo", t)
        self.assertEqual(len(at.get("iframe")), 0)  # la ficha se abre con «Ver ruta»
        self.assertEqual(len([b for b in at.button if b.key and b.key.startswith("ver_")]), 12)

    def test_nombre_obligatorio_antes_de_explorar(self):
        at = nueva(registrado=False)
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(at.get("iframe")), 0)
        self.assertNotIn("Escribe tu nombre para comenzar", texto(at))
        self.assertEqual(at.text_input(key="alias_borrador").label, "¿Cómo te llamas?")
        at.text_input(key="alias_borrador").set_value("Ana María")
        at.button(key="guardar_alias").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(at.session_state["alias_sesion"], "Ana María")
        self.assertIn("Hola, Ana María", texto(at))
        self.assertTrue([b for b in at.button if b.key and b.key.startswith("ver_")])

    def test_nombre_vacio_no_entra_y_avisa(self):
        at = nueva(registrado=False)
        at.text_input(key="alias_borrador").set_value("   ").run()
        at.button(key="guardar_alias").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(at.get("iframe")), 0)
        self.assertIn("Escribe un nombre con al menos una letra", texto(at))

    def test_cambiar_nombre_vuelve_a_la_bienvenida(self):
        at = nueva()
        at.button(key="cambiar_alias").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(at.get("iframe")), 0)
        self.assertNotIn("Escribe tu nombre para comenzar", texto(at))
        self.assertEqual(at.text_input(key="alias_borrador").label, "¿Cómo te llamas?")

    def test_ver_ruta_abre_la_ficha_y_volver_regresa_a_la_lista(self):
        at = nueva(mostrar_todas=True)
        at.button(key="ver_R003").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(at.get("iframe")), 1)
        self.assertTrue(any("Cascada Cóndor Machay" in str(s.value) for s in at.subheader))
        at.button(key="volver_lista").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(at.get("iframe")), 0)

    def test_mostrar_todas_las_rutas(self):
        at = nueva()
        at.button(key="mostrar_todas_btn").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len([b for b in at.button if b.key and b.key.startswith("ver_")]), 20)

    def test_las_20_tarjetas_y_el_reparto_12_6_2(self):
        at = nueva(mostrar_todas=True)
        html = "".join(str(e.value) for e in at.markdown if '<div class="tarjeta' in str(e.value))
        self.assertEqual(html.count('<div class="tarjeta'), 20)
        for nivel, n in (("Fácil", 12), ("Moderada", 6), ("Difícil", 2)):
            self.assertEqual(html.count(f"<b>{nivel}</b>"), n, nivel)

    def test_filtro_de_dificultad_y_busqueda_por_nombre(self):
        at = nueva()
        at.selectbox(key="filtro_nivel").select("Difícil").run()
        self.assertFalse(at.exception)
        html = "".join(str(e.value) for e in at.markdown if '<div class="tarjeta' in str(e.value))
        self.assertEqual(html.count('<div class="tarjeta'), 2)
        at.selectbox(key="filtro_nivel").select("Todos").run()
        at.text_input(key="filtro_nombre").set_value("zzzz").run()
        self.assertFalse(at.exception)
        self.assertIn("Ninguna ruta coincide", texto(at))

    def test_la_vista_principal_no_muestra_codigos_emojis_ni_otros_modelos(self):
        for seccion in ("Explorar rutas", "Comparar alternativas"):
            at = nueva(seccion)
            self.assertFalse(at.exception, [e.value for e in at.exception])
            v = visible(at)
            self.assertIsNone(CODIGO_RUTA.search(v), (seccion, CODIGO_RUTA.search(v)))
            self.assertIsNone(EMOJI.search(v), seccion)
            self.assertIsNone(OTROS.search(v), seccion)

    def test_ruta_sensible_muestra_el_aviso_y_las_demas_no(self):
        frase = "Este nivel puede variar si cambian los supuestos del cálculo"
        self.assertIn(frase, texto(nueva(ruta_detalle="R003")))
        self.assertNotIn(frase, texto(nueva(ruta_detalle="R011")))

    def test_r001_muestra_aviso_de_alta_montana_sin_codigos_internos(self):
        at = nueva(ruta_detalle="R001")
        self.assertFalse(at.exception)
        avisos = [w.value for w in at.warning if "T3" in str(w.value)]
        self.assertTrue(avisos)
        self.assertNotIn("I10/E10", avisos[0])

    def test_comparar_muestra_tres_destinos_con_3_2_y_2_alternativas(self):
        at = nueva("Comparar alternativas")
        self.assertFalse(at.exception, [e.value for e in at.exception])
        opciones = at.selectbox(key="destino_comparar").options
        self.assertEqual(len(opciones), 3)
        esperado = {"Yellow House": 3, "Yanacocha": 2, "Mirador Cerro de la Luz": 2}
        for clave, n in esperado.items():
            etiqueta = next(o for o in opciones if clave in o)
            at.selectbox(key="destino_comparar").select(etiqueta).run()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.dataframe[0].value), n, clave)
            self.assertEqual(len([b for b in at.button if b.key and b.key.startswith("abrir_")]), n)

    def test_abrir_una_alternativa_cambia_a_explorar_y_muestra_su_ficha(self):
        at = nueva("Comparar alternativas")
        etiqueta = next(o for o in at.selectbox(key="destino_comparar").options if "Yellow House" in o)
        at.selectbox(key="destino_comparar").select(etiqueta).run()
        at.button(key="abrir_R020").click().run()
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(at.session_state["seccion"], "Explorar rutas")
        self.assertTrue(any("Sendero 3" in str(s.value) for s in at.subheader))

    def test_como_funciona_explica_limites_sin_lista_de_pendientes(self):
        at = nueva("Cómo funciona")
        self.assertFalse(at.exception, [e.value for e in at.exception])
        t = texto(at)
        self.assertIn("distancia total", t)
        self.assertIsNone(OTROS.search(t))
        self.assertNotIn("Qué falta por validar", t)
        self.assertNotIn("Recomendación de salida activa", t)

    def test_clima_opcional_tolera_fallo_de_red_y_la_ruta_sigue_visible(self):
        import clima_rutas as clima
        at = nueva(ruta_detalle="R003")
        with patch.object(clima, "consultar", side_effect=clima.ClimaNoDisponible("sin red")):
            at.button(key="consultar_clima_R003").click().run()
        self.assertFalse(at.exception)
        self.assertIn("El servicio meteorológico no respondió", texto(at))
        self.assertTrue(any("Cascada Cóndor Machay" in str(s.value) for s in at.subheader))

    def test_clima_con_datos_muestra_temperatura_y_precipitacion_por_separado(self):
        import clima_rutas as clima
        puntos = [{"nombre": "Inicio", "lat": -0.2, "lon": -78.5, "elev": 3000.0, "hora_local": "2026-10-23T10:00", "temperatura_c": 20.7,
                   "precipitacion_mm": 1.2, "viento_kmh": 8.0, "condicion": "Lluvia"},
                  {"nombre": "Llegada", "lat": -0.21, "lon": -78.51, "elev": 3100.0, "hora_local": "2026-10-23T10:00", "temperatura_c": 18.0,
                   "precipitacion_mm": 0.0, "viento_kmh": 10.0, "condicion": "Despejado"}]
        at = nueva(ruta_detalle="R003")
        with patch.object(clima, "consultar", return_value=puntos):
            at.button(key="consultar_clima_R003").click().run()
        self.assertFalse(at.exception)
        html = "".join(str(e.value) for e in at.markdown)
        for frase in ("Temperatura", "Precipitación", "20,7 °C", "1,2 mm", "Tiempo estimado"):
            self.assertIn(frase, html)

    def test_recorre_todas_las_rutas_sin_errores(self):
        import vista_rutas as vr
        at = nueva(ruta_detalle="R001")
        for fila in vr.cargar_catalogo():
            if fila["estado_modelado"] == vr.ELEGIBLE:
                at.selectbox(key="ruta_detalle").select(fila["id_ruta"]).run()
                self.assertFalse(at.exception, fila["id_ruta"])


if __name__ == "__main__":
    unittest.main()
