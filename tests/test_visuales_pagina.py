"""Componentes visuales: HTML bien formado, tres niveles distinguibles sin color y sin lenguaje de recomendación."""
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "06_scripts"))
import visuales_pagina as vz  # noqa: E402

SIN_RECOMENDAR = re.compile(r"mejor ruta|te recomendamos|recomendad", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅]")
VOID = {"br", "hr", "img", "input", "meta", "line", "circle", "path", "rect", "polyline", "polygon"}


class Equilibrio(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pila, self.error = [], None

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.pila.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.pila or self.pila.pop() != tag:
            self.error = tag


def equilibrado(html):
    p = Equilibrio()
    p.feed(html)
    return p.error is None and not p.pila


PERFIL = [{"lat": -0.2 + i * 1e-3, "lon": -78.5 + i * 1e-3, "elev": 3000 + 10 * i} for i in range(30)]
PUNTOS = [{"nombre": n, "lat": PERFIL[k]["lat"], "lon": PERFIL[k]["lon"], "elev": 3000, "hora_local": "2026-10-23T10:00",
           "temperatura_c": t, "precipitacion_mm": p, "viento_kmh": 10.0, "condicion": c}
          for n, k, t, p, c in (("Inicio", 0, 20.7, 1.2, "Lluvia"), ("Llegada", -1, 5.0, 0.0, "Condición no especificada"))]
RUTAS = [{"nombre": "Ruta A", "horas": 0.5, "nivel": "Fácil", "sensible": False},
         {"nombre": "Ruta B", "horas": 2.0, "nivel": "Moderada", "sensible": True},
         {"nombre": "Ruta C", "horas": 4.5, "nivel": "Difícil", "sensible": False}]


class Visuales(unittest.TestCase):
    def test_componentes_son_html_equilibrado_sin_emojis_ni_recomendaciones(self):
        piezas = [
            vz.insignia_nivel("Moderada", True), vz.tarjeta_ruta("Ruta A", "Lugar", "Fácil", 1.2, 80, "Ida y vuelta", "Aviso"),
            vz.rejilla([vz.tarjeta_ruta("A", "L", "Difícil", 9, 800, "Circuito")], 2), vz.escala_esfuerzo(2.0, "Moderada"),
            vz.resumen_niveles({"Fácil": 8, "Moderada": 10, "Difícil": 2}), vz.grafico_horas(RUTAS),
            vz.miniperfil([p["elev"] for p in PERFIL]), vz.panel_clima(PERFIL, PUNTOS), vz.flujo([("a", "b")]),
            vz.avisos_ruta(["Altitud"], ["Acceso uno", "Acceso dos"], ["No requiere equipo"]),
            vz.barras_relativas([{"etiqueta": "A", "x": 1}, {"etiqueta": "B", "x": 3}], "x", "T", "km"),
            vz.teselas([("bajada", "1", "m", "Bajada")]), vz.tabla_html(["a"], [["b"]]),
        ]
        for html in piezas:
            self.assertTrue(equilibrado(html), html[:90])
            self.assertIsNone(SIN_RECOMENDAR.search(html))
            self.assertIsNone(EMOJI.search(html))
            self.assertNotIn("\n\n", html)

    def test_los_niveles_se_distinguen_por_texto_y_por_numero_de_barras(self):
        for nivel, llenas in (("Fácil", 1), ("Moderada", 2), ("Difícil", 3)):
            html = vz.insignia_nivel(nivel)
            self.assertIn(f"<b>{nivel}</b>", html)
            self.assertEqual(html.count('fill-opacity="1"'), llenas)
        with self.assertRaises(ValueError):
            vz.insignia_nivel("Extrema")

    def test_una_sola_etiqueta_principal_con_el_rotulo_pedido(self):
        html = vz.insignia_nivel("Fácil")
        self.assertIn("Dificultad física estimada:", html)
        self.assertEqual(html.count("<b>"), 1)

    def test_el_aviso_de_sensibilidad_usa_la_frase_acordada(self):
        self.assertIn("La categoría cambia en algunos escenarios metodológicos", vz.insignia_nivel("Moderada", True))
        self.assertNotIn("sensible", vz.insignia_nivel("Moderada", False))

    def test_la_tarjeta_reserva_el_area_de_aviso_aunque_este_vacia(self):
        self.assertIn('<div class="t-aviso"></div>', vz.tarjeta_ruta("A", "L", "Fácil", 1, 1, "Circuito"))

    def test_muestra_centésimas_cerca_del_límite_de_una_hora(self):
        ruta = {"nombre": "Ruta cerca del límite", "horas": 1.0113, "nivel": "Moderada"}
        self.assertIn("1,01 h · Moderada", vz.grafico_horas([ruta]))
        self.assertIn("Moderada: 1,01 horas", vz.escala_esfuerzo(1.0113, "Moderada"))

    def test_los_avisos_dan_mas_espacio_al_acceso_y_escapan_html(self):
        html = vz.avisos_ruta(["3 000 m"], ["Aviso largo", "<script>x</script>"], ["No"])
        self.assertLess(html.index("Acceso y estado"), html.index("Altitud"))
        self.assertEqual(html.count('<section class="aviso-card'), 3)
        self.assertNotIn("<script>", html)

    def test_el_clima_separa_temperatura_precipitacion_y_condicion(self):
        html = vz.panel_clima(PERFIL, PUNTOS)
        for frase in ("Temperatura", "Precipitación", "Viento", "Condición según el modelo", "20,7 °C", "1,2 mm", "Lluvia", "Válido:"):
            self.assertIn(frase, html)
        self.assertNotRegex(html, r"calor|frío|caluroso")
        self.assertEqual(html.count("clima-dato-et"), 6)

    def test_escapa_html_en_nombres(self):
        self.assertNotIn("<script", vz.tarjeta_ruta("<script>x</script>", "L", "Fácil", 1, 1, "Circuito"))
        self.assertNotIn("<script", vz.grafico_horas([{"nombre": "<script>", "horas": 1, "nivel": "Fácil"}]))

    def test_icono_clima_tolera_condiciones_desconocidas(self):
        self.assertIn("<svg", vz.icono_clima("algo raro"))


if __name__ == "__main__":
    unittest.main()


class PlantillaVisorCapasTest(unittest.TestCase):
    """El visor ofrece solo Calles y Satélite; no queda rastro de la capa topográfica retirada."""

    @classmethod
    def setUpClass(cls):
        ruta = Path(__file__).resolve().parents[1] / "06_scripts" / "visor_ruta" / "plantilla.html"
        cls.html = ruta.read_text(encoding="utf-8")

    def test_botones_de_capa_son_solo_calles_y_satelite(self):
        import re
        capas = re.findall(r'data-capa="([a-z]+)"', self.html)
        self.assertEqual(capas, ["calles", "satelite"])
        self.assertNotIn("Topográfico", self.html)

    def test_sin_referencias_a_opentopomap(self):
        self.assertNotIn("opentopomap", self.html.lower())
        self.assertNotIn("capas.topo", self.html)

    def test_conserva_las_atribuciones_de_las_dos_capas(self):
        self.assertIn("OpenStreetMap", self.html)
        self.assertIn("Esri", self.html)
