"""Clasificación pública relativa de tres grupos K-means en la página."""

import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tests"))
sys.path.insert(0, str(RAIZ / "06_scripts"))
from test_app_humo import CODIGO_RUTA, EMOJI, ejecutar  # noqa: E402
import vista_rutas as vr  # noqa: E402

SENSIBLES = {"R003", "R006", "R015", "R019", "R022", "R023"}
OTROS_NIVELES = re.compile(r"dbscan|\bward\b|\bhen\b|índice de esfuerzo", re.I)
SIN_RECOMENDAR = re.compile(r"mejor ruta|te recomendamos|recomendada", re.I)


def nombre(id_ruta):
    return next(f["nombre_ruta"] for f in vr.cargar_catalogo() if f["id_ruta"] == id_ruta)


class TresNiveles(unittest.TestCase):
    def test_las_20_rutas_tienen_una_categoria_kmeans_y_el_reparto_es_12_6_2(self):
        cat = vr.cargar_catalogo()
        niveles = [vr.clasificacion_kmeans_k3(cat)[f["id_ruta"]]["nivel"] for f in cat if f["estado_modelado"] == vr.ELEGIBLE]
        self.assertEqual(len(niveles), 20)
        self.assertEqual({n: niveles.count(n) for n in ("Fácil", "Moderada", "Difícil")}, {"Fácil": 12, "Moderada": 6, "Difícil": 2})

    def test_kmeans_es_la_fuente_publica_y_la_regla_queda_como_contraste(self):
        catalogo = vr.cargar_catalogo()
        modelo = vr.clasificacion_kmeans_k3(catalogo)
        discrepancias = {id_ruta for id_ruta, grupo in modelo.items()
                         if grupo["nivel"] != vr.dificultad_fisica_estimada(id_ruta, catalogo)["nivel"]}
        self.assertEqual(discrepancias, {"R004", "R015", "R023", "R026"})
        st = ejecutar(valores={"ruta_detalle": "R004"})
        self.assertIn("K-means agrupó 20 recorridos", st.textos(visibles=False))
        self.assertIn("la clasifica como Moderada", st.textos(visibles=False))

    def test_modelo_rechaza_muestra_o_medidas_alteradas(self):
        catalogo = vr.cargar_catalogo()
        alterado = [dict(f) for f in catalogo]
        elegible = next(f for f in alterado if f["id_ruta"] == "R004")
        elegible["distancia_total_km"] = "999"
        with self.assertRaisesRegex(ValueError, "difiere"):
            vr.clasificacion_kmeans_k3(alterado)
        elegible["estado_modelado"] = "no_elegible_aun"
        with self.assertRaisesRegex(ValueError, "no corresponden"):
            vr.clasificacion_kmeans_k3(alterado)

    def test_explorar_empieza_con_12_tarjetas_y_un_boton_para_ver_el_resto(self):
        st = ejecutar()
        self.assertEqual(len(st.tarjetas()), 12)
        claves = [k.get("key") for a, k in st.llamadas_de("button")]
        self.assertEqual(len([c for c in claves if str(c).startswith("ver_")]), 12)
        self.assertIn("mostrar_todas_btn", claves)
        self.assertEqual(st.llamadas_de("iframe"), [])  # la ficha se abre al pulsar «Ver ruta»

    def test_ver_ruta_abre_la_ficha_con_boton_para_volver(self):
        st = ejecutar(valores={"ruta_detalle": "R003"})
        claves = [k.get("key") for a, k in st.llamadas_de("button")]
        self.assertIn("volver_lista", claves)
        self.assertFalse([c for c in claves if str(c).startswith("ver_")])
        self.assertEqual(len(st.llamadas_de("iframe")), 1)

    def test_explorar_muestra_20_tarjetas_con_una_sola_etiqueta_principal(self):
        st = ejecutar(valores={"mostrar_todas": True})
        tarjetas = st.tarjetas()
        self.assertEqual(len(tarjetas), 20)
        for t in tarjetas:
            self.assertEqual(len(re.findall(r"<b>(Fácil|Moderada|Difícil)</b>", t)), 1)
        conteo = {n: sum(f"<b>{n}</b>" in t for t in tarjetas) for n in ("Fácil", "Moderada", "Difícil")}
        self.assertEqual(conteo, {"Fácil": 12, "Moderada": 6, "Difícil": 2})
        self.assertIn("Dificultad física relativa", st.textos() + st.html())

    def test_la_vista_principal_no_muestra_codigos_emojis_ni_modelos_secundarios(self):
        for seccion in ("Explorar rutas", "Comparar alternativas"):
            st = ejecutar(seccion)
            todo = st.textos() + st.html()
            self.assertIsNone(CODIGO_RUTA.search(re.sub(r"<[^>]+>", "", todo)), (seccion, CODIGO_RUTA.search(todo)))
            self.assertIsNone(EMOJI.search(todo), seccion)
            self.assertIsNone(OTROS_NIVELES.search(todo), (seccion, OTROS_NIVELES.search(todo)))
            self.assertIsNone(SIN_RECOMENDAR.search(todo))

    def test_todas_las_rutas_se_pueden_abrir_sin_codigos_visibles(self):
        for fila in vr.cargar_catalogo():
            if fila["estado_modelado"] != vr.ELEGIBLE:
                continue
            st = ejecutar(valores={"ruta_detalle": fila["id_ruta"]})
            self.assertEqual(len(st.llamadas_de("iframe")), 1, fila["id_ruta"])
            self.assertEqual(len(st.llamadas_de("download_button")), 2)
            visible = st.textos() + re.sub(r"<[^>]+>", "", st.html())
            self.assertIsNone(CODIGO_RUTA.search(visible), (fila["id_ruta"], CODIGO_RUTA.search(visible)))
            self.assertIn(fila["nombre_ruta"], visible)

    def test_aviso_de_categoria_sensible_solo_en_las_seis_rutas(self):
        frase = "La categoría cambia en al menos una prueba de sensibilidad del modelo"
        for fila in vr.cargar_catalogo():
            if fila["estado_modelado"] != vr.ELEGIBLE:
                continue
            texto = ejecutar(valores={"ruta_detalle": fila["id_ruta"]}).textos()
            self.assertEqual(frase in texto, fila["id_ruta"] in SENSIBLES, fila["id_ruta"])

    def test_filtros_por_dificultad_lugar_y_nombre(self):
        self.assertEqual(len(ejecutar(valores={"filtro_nivel": "Difícil"}).tarjetas()), 2)
        self.assertEqual(len(ejecutar(valores={"filtro_nivel": "Fácil"}).tarjetas()), 12)
        self.assertEqual(len(ejecutar(valores={"filtro_lugar": "Mindo"}).tarjetas()), 5)
        cascadas = ejecutar(valores={"filtro_nombre": "cascada"}).tarjetas()
        self.assertTrue(cascadas and all("ascada" in t for t in cascadas))
        vacio = ejecutar(valores={"filtro_nombre": "zzzz"})
        self.assertIn("Ninguna ruta coincide", vacio.textos())
        self.assertEqual(vacio.llamadas_de("iframe"), [])

    def test_las_tarjetas_comparten_estructura_y_aviso_solo_cuando_corresponde(self):
        st = ejecutar(valores={"mostrar_todas": True})
        for t in st.tarjetas():
            for parte in ('class="t-lugar"', 'class="t-nombre"', 't-nivel', 'class="t-datos"', 'class="t-tipo"', 'class="t-aviso"'):
                self.assertIn(parte, t)
        con_aviso = [t for t in st.tarjetas() if re.search(r'class="t-aviso">[^<]', t)]
        self.assertEqual(len(con_aviso), 12)

    def test_rucu_pichincha_conserva_el_aviso_de_alta_montana_separado_de_la_categoria(self):
        st = ejecutar(valores={"ruta_detalle": "R001"})
        avisos = [a[0] for n, a, k, _ in st.llamadas if n == "warning" and a and "T3" in a[0]]
        self.assertTrue(avisos)
        self.assertNotIn("I10/E10", avisos[0])
        self.assertNotIn("clase física", avisos[0])
        t = st.textos()
        self.assertIn("Difícil", st.html())
        self.assertIn("independientes de la categoría", t)

    def test_la_explicacion_kmeans_esta_en_la_ficha_sin_umbrales_de_horas(self):
        st = ejecutar(valores={"ruta_detalle": "R003"})
        self.assertTrue(any(n == "expander" and a[0] == "Cómo se obtuvo esta categoría" for n, a, k, _ in st.llamadas))
        self.assertIn("K-means agrupó 20 recorridos", st.textos(visibles=False))
        self.assertNotIn('class="escala"', st.html())

    def test_el_clima_es_secundario_y_va_en_un_desplegable(self):
        st = ejecutar(valores={"ruta_detalle": "R003"})
        etiquetas = [a[0] for n, a, k, _ in st.llamadas if n == "expander"]
        self.assertIn("Clima estimado cerca del recorrido (opcional)", etiquetas)
        self.assertLess(etiquetas.index("Cómo se obtuvo esta categoría"), etiquetas.index("Clima estimado cerca del recorrido (opcional)"))
        self.assertTrue(any(n == "button" and a and a[0] == "Consultar clima de esta ruta" for n, a, k, _ in st.llamadas))


class CompararAlternativas(unittest.TestCase):
    DESTINOS = {"Yellow House": 3, "Extremo común de los senderos de Yanacocha": 2, "Mirador Cerro de la Luz": 2}

    def test_solo_hay_tres_destinos_con_varias_alternativas(self):
        st = ejecutar("Comparar alternativas")
        etiquetas = st.opciones["destino_comparar"]
        self.assertEqual(len(etiquetas), 3)
        for destino, n in self.DESTINOS.items():
            self.assertTrue(any(destino in e and f"{n} alternativas" in e for e in etiquetas), (destino, etiquetas))

    def test_cada_destino_muestra_sus_alternativas_ordenadas_y_ninguna_ajena(self):
        for destino, n in self.DESTINOS.items():
            etiqueta = next(e for e in ejecutar("Comparar alternativas").opciones["destino_comparar"] if destino in e)
            st = ejecutar("Comparar alternativas", {"destino_comparar": etiqueta})
            self.assertEqual(len(st.tarjetas()), n)
            filas = st.llamadas_de("dataframe")[0][0][0]
            self.assertEqual(len(filas), n)
            self.assertEqual({f["Destino exacto"] for f in filas}, {destino})
            self.assertEqual(len(st.llamadas_de("iframe")), 0)

    def test_yellow_house_orden_por_esfuerzo_estimado_sin_codigos(self):
        etiqueta = next(e for e in ejecutar("Comparar alternativas").opciones["destino_comparar"] if "Yellow House" in e)
        filas = ejecutar("Comparar alternativas", {"destino_comparar": etiqueta}).llamadas_de("dataframe")[0][0][0]
        self.assertEqual([f["Ruta"] for f in filas], [nombre("R017"), nombre("R021"), nombre("R020")])
        self.assertTrue(all(f["Dificultad física estimada"].startswith("Moderada") for f in filas))

    def test_los_destinos_de_una_sola_ruta_no_generan_comparacion(self):
        st = ejecutar("Comparar alternativas")
        self.assertIn("una sola ruta elegible", st.textos())
        self.assertNotIn("Ilaló", "".join(st.opciones["destino_comparar"]))
        self.assertNotIn("Pondoña", "".join(st.opciones["destino_comparar"]))

    def test_los_botones_abrir_detalle_existen_para_cada_alternativa(self):
        etiqueta = next(e for e in ejecutar("Comparar alternativas").opciones["destino_comparar"] if "Yellow House" in e)
        st = ejecutar("Comparar alternativas", {"destino_comparar": etiqueta})
        claves = [k.get("key") for n, a, k, _ in st.llamadas
                  if n == "button" and str(k.get("key", "")).startswith("abrir_")]
        self.assertEqual(sorted(claves), ["abrir_R017", "abrir_R020", "abrir_R021"])


class Metodologia(unittest.TestCase):
    def test_explica_kmeans_categorias_y_sensibilidad_sin_lista_de_pendientes(self):
        st = ejecutar("Metodología y límites")
        html = st.html(visibles=False)
        todo = html + st.textos(visibles=False)
        for frase in ("no es el método MIDE completo", "K-means", "k=3", "distancia total", "subida acumulada", "6 rutas cambian"):
            self.assertIn(frase, todo, frase)
        self.assertNotIn("Qué falta por validar", todo)
        self.assertNotIn("Recomendación de salida activa", todo)
        self.assertIn("esfuerzo físico relativo", todo)
        self.assertEqual(len(re.findall(r'class="hg-fila"', html)), 20)

    def test_los_contrastes_dbscan_y_hen_solo_aparecen_en_el_detalle_metodologico(self):
        st = ejecutar("Metodología y límites")
        contrastes = [(a, p) for n, a, k, p in st.llamadas if n == "markdown" and "Contrastes metodológicos (para quien revisa la tesis)" in p]
        self.assertTrue(contrastes)
        self.assertIn("DBSCAN", st.textos(visibles=False) + st.html(visibles=False))

    def test_no_se_habilitan_recomendaciones(self):
        self.assertFalse(vr.NIVELES_FINALES.exists())
        self.assertEqual(vr.conteo_estados(vr.cargar_catalogo())["habilitadas_recomendacion"], 0)
        todo = ejecutar("Metodología y límites").textos()
        self.assertIsNone(SIN_RECOMENDAR.search(todo))


if __name__ == "__main__":
    unittest.main()
