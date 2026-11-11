"""Prueba de humo de app.py con un Streamlit simulado.

Comprueba la lógica de la página (secciones, filtros, tarjetas, comparación, textos, estados vacíos) pero NO valida
las firmas de la API real de Streamlit: eso se hace con test_app_streamlit_real.py y ejecutando `streamlit run app.py`.
"""

import re
import runpy
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆✅❗]")
CODIGO_RUTA = re.compile(r"\bR\d{3}\b")
VISIBLES = {"markdown", "caption", "write", "subheader", "info", "warning", "success", "error", "metric"}
TECNICOS = ("Datos técnicos",)


class Contexto:
    """Contexto simulado para `with st.container():`, columnas y expanders; recuerda en qué expander está cada llamada."""

    def __init__(self, pagina, etiqueta=None):
        self._pagina = pagina
        self._etiqueta = etiqueta

    def __enter__(self):
        self._pagina._pila.append(self._etiqueta)
        return self

    def __exit__(self, *exc):
        self._pagina._pila.pop()
        return False

    def __getattr__(self, nombre):
        return getattr(self._pagina, nombre)


class StreamlitFalso:
    """Registra lo que la página pide mostrar y devuelve los valores elegidos por la prueba."""

    def __init__(self, seccion=None, valores=None, registrado=True):
        self.llamadas = []
        self.session_state = {"alias_sesion": "Usuario de prueba"} if registrado else {}
        if seccion:
            self.session_state["seccion"] = seccion
        self.valores = dict(valores or {})
        for clave in ("ruta_detalle", "mostrar_todas"):  # estado que en la app real ponen los botones
            if clave in self.valores:
                self.session_state[clave] = self.valores[clave]
        self.opciones = {}
        self._pila = []
        self.detenido = False

    def _reg(self, nombre, *args, **kwargs):
        self.llamadas.append((nombre, args, kwargs, tuple(e for e in self._pila if e)))

    def textos(self, visibles=True):
        """Texto que ve la persona. Se excluyen los desplegables técnicos, que sí pueden citar identificadores internos."""
        salida = []
        for nombre, args, kwargs, pila in self.llamadas:
            if nombre == "markdown" and args and str(args[0]).startswith("<style>"):
                continue
            if visibles and (nombre not in VISIBLES or any(p.startswith(TECNICOS) for p in pila)):
                continue
            salida += [a for a in args if isinstance(a, str)]
            salida += [kwargs["help"] for _ in [0] if isinstance(kwargs.get("help"), str)]
        return "\n".join(salida)

    def llamadas_de(self, nombre):
        return [(a, k) for n, a, k, _ in self.llamadas if n == nombre]

    def html(self, *args, visibles=True, **kwargs):
        """Sin argumentos: HTML de los bloques markdown, sin la hoja de estilos (y sin los desplegables técnicos si `visibles`).
        Con argumentos: es la llamada `st.html(...)` de la página y solo se registra (galería, ayuda de desplazamiento)."""
        if args:
            self._reg("html", *args, **kwargs)
            return None
        return "".join(a[0] for n, a, k, p in self.llamadas if n == "markdown" and a and not a[0].startswith("<style>")
                       and not (visibles and any(e.startswith(TECNICOS) for e in p)))

    def tarjetas(self):
        """Tarjetas HTML de rutas mostradas (en la lista de Explorar o en la rejilla de Comparar)."""
        return "".join(a[0] for n, a, k, _ in self.llamadas if n == "markdown" and a and '<div class="tarjeta' in a[0]).split('<div class="tarjeta')[1:]

    def __getattr__(self, nombre):
        if nombre in ("cache_data", "cache_resource"):
            return lambda f=None, **k: (f if f else (lambda g: g))
        if nombre == "columns":
            return lambda n, *a, **k: [Contexto(self) for _ in range(n if isinstance(n, int) else len(n))]
        if nombre in ("container", "form"):
            return lambda *a, **k: (self._reg(nombre, *a, **k), Contexto(self))[1]
        if nombre == "expander":
            return lambda etiqueta, *a, **k: (self._reg(nombre, etiqueta, *a, **k), Contexto(self, etiqueta))[1]
        if nombre in ("selectbox", "segmented_control"):
            def elegir(etiqueta, opciones, *a, **k):
                opciones = list(opciones)
                clave = k.get("key")
                self.opciones[clave] = opciones
                self._reg(nombre, etiqueta, **{x: y for x, y in k.items() if isinstance(y, str)})
                if clave in self.valores and self.valores[clave] in opciones:
                    elegido = self.valores[clave]
                elif self.session_state.get(clave) in opciones:
                    elegido = self.session_state[clave]
                else:
                    elegido = opciones[0]
                if clave:
                    self.session_state[clave] = elegido
                return elegido
            return elegir
        if nombre == "text_input":
            return lambda etiqueta, *a, **k: (self._reg("text_input", etiqueta, key=k.get("key")),
                                              self.valores.get(k.get("key"), ""))[1]
        if nombre == "number_input":
            return lambda etiqueta, *a, **k: self.valores.get(k.get("key"), k.get("value", 0.0))
        if nombre in ("button", "form_submit_button"):
            return lambda *a, **k: (self._reg("button", *a, **{x: y for x, y in k.items() if x == "key"}), False)[1]
        if nombre == "html":
            return lambda *a, **k: self._reg(nombre, *a, **k)
        if nombre == "stop":
            def stop():
                self.detenido = True
                raise SystemExit
            return stop
        return lambda *a, **k: self._reg(nombre, *a, **k)


def ejecutar(seccion=None, valores=None, parchear=None, registrado=True):
    falso = StreamlitFalso(seccion, valores, registrado)
    sys.path.insert(0, str(RAIZ / "06_scripts"))
    nombres = ("vista_rutas", "datos_mapa_dashboard", "visuales_pagina")
    try:
        with mock.patch.dict(sys.modules, {"streamlit": falso}):
            for nombre in nombres:
                sys.modules.pop(nombre, None)
            try:
                if parchear:
                    parchear()
                runpy.run_path(str(RAIZ / "app.py"), run_name="__main__")
            except SystemExit:
                pass
            finally:
                for nombre in nombres:
                    sys.modules.pop(nombre, None)
    finally:
        sys.path.remove(str(RAIZ / "06_scripts"))
    return falso


class AppHumo(unittest.TestCase):
    def test_portada_responde_la_pregunta_sin_aviso_de_desarrollo(self):
        st = ejecutar()
        html = st.html()
        self.assertIn("Elige tu próxima caminata sabiendo cuánto esfuerzo te espera", html)
        self.assertIn("Explorar las 20 rutas", html)
        self.assertEqual(len(st.llamadas_de("iframe")), 0)  # la galería usa st.html; el único iframe es el visor de la ficha
        galerias = [a[0] for a, k in st.llamadas_de("html") if 'class="gal"' in a[0]]
        self.assertEqual(len(galerias), 1)
        self.assertEqual(galerias[0].count('class="gal-slide'), 6)
        self.assertFalse(st.llamadas_de("html")[0][1].get("unsafe_allow_javascript", False))
        self.assertIn("20 rutas", html)
        self.assertNotIn("Versión en desarrollo", st.textos())

    def test_sin_nombre_pide_ingreso_y_no_muestra_rutas(self):
        st = ejecutar(registrado=False)
        self.assertTrue(st.detenido)
        self.assertNotIn("Escribe tu nombre para comenzar", "\n".join(st.textos()))
        etiquetas = [args[0] for nombre, args, kwargs, pila in st.llamadas if nombre == "text_input" and args]
        self.assertIn("¿Cómo te llamas?", etiquetas)
        self.assertEqual(st.tarjetas(), [])

    def test_bienvenida_usa_formulario_para_enviar_con_enter(self):
        st = ejecutar(registrado=False)
        self.assertEqual(len(st.llamadas_de("form")), 1)
        botones = [k.get("key") for a, k in st.llamadas_de("button")]
        self.assertIn("guardar_alias", botones)
        html = st.html()
        self.assertIn("Rutas de trekking en Pichincha", html)
        self.assertNotIn("No necesitas cuenta ni contraseña", st.textos())
        self.assertIsNone(EMOJI.search(html + st.textos()))

    def test_saludo_escapa_el_nombre_y_permite_cambiarlo(self):
        st = ejecutar()
        self.assertIn("Hola, Usuario de prueba.", st.html())
        self.assertIn("cambiar_alias", [k.get("key") for a, k in st.llamadas_de("button")])

    def test_metodologia_explica_la_regla_sin_lista_de_pendientes(self):
        texto = ejecutar("Metodología y límites").textos()
        self.assertIn("K-means con **k=3**", texto)
        self.assertNotIn("Qué falta por validar", texto)
        self.assertNotIn("Recomendación de salida activa", texto)

    def test_sin_rutas_elegibles_muestra_estado_vacio_y_no_falla(self):
        def sin_elegibles():
            import datos_mapa_dashboard as d
            original = d.cargar_catalogo
            d.cargar_catalogo = lambda *a, **k: [dict(f, estado_modelado="no_elegible_aun") for f in original(*a, **k)]

        st = ejecutar(parchear=sin_elegibles)
        self.assertIn("No hay alternativas elegibles", st.textos())
        self.assertEqual(st.llamadas_de("iframe"), [])

    def test_web_app_ejecuta_el_mismo_app_raiz(self):
        codigo = (RAIZ / "web" / "app.py").read_text(encoding="utf-8")
        self.assertIn('run_path(str(Path(__file__).resolve().parents[1] / "app.py")', codigo)


if __name__ == "__main__":
    unittest.main()
