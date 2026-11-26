"""Índice de esfuerzo de referencia en la página: descriptivo, solo dentro del mismo destino exacto."""

import re
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "06_scripts"))
sys.path.insert(0, str(RAIZ / "tests"))
import vista_rutas as vr  # noqa: E402

PROHIBIDAS = re.compile(r"f[aá]cil|dif[ií]cil|moderad|nivel (bajo|medio|alto)|exigencia (baja|media|alta)|mejor ruta|recomendad", re.IGNORECASE)
TEXTOS = (vr.ROTULO_INDICE, vr.AVISO_INDICE, vr.AVISO_ORDEN, vr.AVISO_SENSIBILIDAD)


def todas():
    catalogo, destinos = vr.cargar_catalogo(), vr.cargar_destinos()
    for lugar in vr.lugares(catalogo, destinos):
        for d in vr.destinos_de_lugar(catalogo, lugar["lugar"], destinos):
            yield lugar["lugar"], d["destino"], vr.alternativas_de_destino(catalogo, lugar["lugar"], d["destino"], destinos)


class IndiceEsfuerzo(unittest.TestCase):
    def test_formula_y_rotulo(self):
        self.assertAlmostEqual(vr.horas_equivalentes(10, 600), 3.0)
        self.assertEqual(vr.ROTULO_INDICE, "Índice de esfuerzo de referencia (h-eq)")
        fila = {"distancia_total_km": "5.0", "ascenso_total_m": "300"}
        r = vr.indice_esfuerzo(fila)
        self.assertAlmostEqual(r["valor"], 1.5)
        self.assertAlmostEqual(r["parte_distancia"] + r["parte_ascenso"], r["valor"])

    def test_el_indice_no_depende_de_la_altitud(self):
        base = {"distancia_total_km": "4", "ascenso_total_m": "250", "elevacion_max_m": "1500"}
        alta = dict(base, elevacion_max_m="4700")
        self.assertEqual(vr.indice_esfuerzo(base), vr.indice_esfuerzo(alta))

    def test_textos_no_hablan_de_duracion_prevista_ni_de_clases_ni_de_mejor(self):
        for t in TEXTOS:
            self.assertIsNone(PROHIBIDAS.search(t), t)
        self.assertIn("No es la duración prevista", vr.AVISO_INDICE)
        self.assertIn("no es un intervalo de confianza", vr.AVISO_SENSIBILIDAD)
        self.assertIn("No indica cuál alternativa elegir", vr.AVISO_ORDEN)

    def test_el_orden_solo_existe_dentro_de_un_destino_exacto(self):
        for lugar, destino, alts in todas():
            ordenadas = vr.ordenar_por_indice(alts)
            valores = [vr.indice_esfuerzo(a)["valor"] for a in ordenadas]
            self.assertEqual(valores, sorted(valores), (lugar, destino))
            self.assertEqual({a["id_ruta"] for a in ordenadas}, {a["id_ruta"] for a in alts})
            self.assertEqual({(a["lugar"], a["destino_exacto"]) for a in ordenadas}, {(lugar, destino)})

    def test_ordenar_destinos_distintos_falla(self):
        cat, des = vr.cargar_catalogo(), vr.cargar_destinos()
        a = vr.alternativas_de_destino(cat, "Cerro Ilaló", "Cima del Cerro Ilaló", des)
        b = vr.alternativas_de_destino(cat, "Cerro Ilaló", "Cruz del Ilaló", des)
        with self.assertRaises(ValueError):
            vr.ordenar_por_indice(a + b)

    def test_yellow_house_orden_conocido(self):
        cat, des = vr.cargar_catalogo(), vr.cargar_destinos()
        alts = vr.ordenar_por_indice(vr.alternativas_de_destino(cat, "Mindo", "Yellow House", des))
        self.assertEqual([a["id_ruta"] for a in alts], ["R017", "R021", "R020"])

    def test_empate_se_desempata_por_identificador(self):
        a = {"id_ruta": "R002", "lugar": "L", "destino_exacto": "D", "distancia_total_km": "5", "ascenso_total_m": "300"}
        b = dict(a, id_ruta="R001")
        self.assertEqual([x["id_ruta"] for x in vr.ordenar_por_indice([a, b])], ["R001", "R002"])


class SensibilidadDEM(unittest.TestCase):
    def test_crudo_se_calcula_con_la_convencion_del_dataset(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "R999_perfil_elevacion_raw_2026-01-01.csv"
            ruta.write_text("id_ruta,elevacion_m\nR999,100\nR999,110\nR999,105\nR999,120\n", encoding="utf-8")
            self.assertAlmostEqual(vr.ascenso_crudo_total("R999", "ida_y_vuelta", Path(d)), 30.0)  # 25 de subida + 5 de bajada
            self.assertAlmostEqual(vr.ascenso_crudo_total("R999", "circular", Path(d)), 25.0)

    def test_perfil_crudo_inexistente_o_id_invalido(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                vr.ascenso_crudo_total("R998", "ida_y_vuelta", Path(d))
        with self.assertRaises(ValueError):
            vr.ruta_perfil_crudo("../R001")

    def test_filtrado_reproduce_el_dataset_y_crudo_nunca_es_menor(self):
        for _, _, alts in todas():
            for fila in alts:
                s = vr.sensibilidad_dem(fila)
                self.assertAlmostEqual(s["ascenso_filtrado_m"], float(fila["ascenso_total_m"]))
                self.assertGreaterEqual(s["ascenso_crudo_m"], s["ascenso_filtrado_m"] - 1e-6, fila["id_ruta"])
                self.assertGreaterEqual(s["indice_crudo"], s["indice_filtrado"] - 1e-9)
                self.assertAlmostEqual(s["indice_filtrado"], vr.indice_esfuerzo(fila)["valor"])


class AvisosSeparados(unittest.TestCase):
    def test_ningun_aviso_se_pierde_y_las_tres_categorias_existen(self):
        inv, ver = vr.cargar_inventario(), vr.cargar_verificacion()
        for _, _, alts in todas():
            for fila in alts:
                sep = vr.avisos_separados(fila["id_ruta"], fila, inv, ver)
                self.assertEqual(set(sep), {"altitud", "acceso", "caracter_tecnico", "otros"})
                for categoria in ("altitud", "acceso", "caracter_tecnico"):
                    self.assertTrue(sep[categoria], (fila["id_ruta"], categoria))
                mostrados = {t for lista in sep.values() for t in lista}
                for texto in vr.advertencias(fila["id_ruta"], ver):
                    self.assertIn(texto, mostrados, fila["id_ruta"])

    def test_altitud_se_informa_como_valor_y_no_entra_en_el_indice(self):
        inv, ver = vr.cargar_inventario(), vr.cargar_verificacion()
        cat, des = vr.cargar_catalogo(), vr.cargar_destinos()
        fila = vr.alternativas_de_destino(cat, "Rucu Pichincha", "Cumbre del Rucu Pichincha por el sendero del arenal", des)[0]
        sep = vr.avisos_separados("R001", fila, inv, ver)
        self.assertIn("4 679 m", sep["altitud"][0])
        self.assertIn("No forma parte del índice", sep["altitud"][0])
        self.assertTrue(any("T3" in t for t in sep["caracter_tecnico"]))
        aviso = next(t for t in vr.advertencias("R001", ver) if "T3" in t)
        self.assertEqual(sum(aviso in lista for lista in sep.values()), 1)

    def test_acceso_y_caracter_tecnico_conocidos(self):
        inv, ver = vr.cargar_inventario(), vr.cargar_verificacion()
        cat, des = vr.cargar_catalogo(), vr.cargar_destinos()
        por_id = {f["id_ruta"]: f for f in cat if f["estado_modelado"] == vr.ELEGIBLE}
        r026 = vr.avisos_separados("R026", por_id["R026"], inv, ver)
        self.assertTrue(any("tarabita" in t.lower() for t in r026["acceso"]))
        self.assertFalse(any("tarabita" in t.lower() for t in r026["caracter_tecnico"]))
        r022 = vr.avisos_separados("R022", por_id["R022"], inv, ver)
        self.assertTrue(any("vados" in t for t in r022["caracter_tecnico"]))
        self.assertTrue(any("vados" in t for t in r022["acceso"]))
        self.assertTrue(vr.avisos_separados("R011", por_id["R011"], inv, ver)["otros"])  # trazado por confirmar

    def test_categoria_desconocida_se_rechaza(self):
        fila = {"elevacion_max_m": "1000"}
        with self.assertRaises(ValueError):
            vr.avisos_separados("R001", fila, {}, [], [{"clave": "R001", "tipo": "advertencia", "categoria": "inventada", "nota": ""}])

    def test_el_archivo_de_categorias_solo_cita_avisos_existentes(self):
        ver = {(r["clave"], r["tipo"]) for r in vr.cargar_verificacion()}
        for c in vr.cargar_categorias():
            self.assertIn((c["clave"], c["tipo"]), ver)
            self.assertIn(c["categoria"], vr.CATEGORIAS)


class ClasesYRecomendacionesSiguenBloqueadas(unittest.TestCase):
    def test_no_existen_archivos_de_habilitacion_ni_se_declara_clasificacion(self):
        self.assertFalse(vr.NIVELES_FINALES.exists())
        self.assertFalse(vr.VALIDACION_MODELO.exists())
        estado = vr.estado_clasificacion(vr.cargar_catalogo())
        self.assertFalse(estado["disponible"])
        self.assertIn("en desarrollo", estado["mensaje"])
        self.assertEqual(vr.conteo_estados(vr.cargar_catalogo())["habilitadas_recomendacion"], 0)

    def test_el_dato_del_indice_no_agrega_campos_de_nivel(self):
        self.assertEqual(set(vr.indice_esfuerzo({"distancia_total_km": "1", "ascenso_total_m": "1"})),
                         {"valor", "parte_distancia", "parte_ascenso"})


class PaginaConStreamlitSimulado(unittest.TestCase):
    """El HEN sigue disponible en la capa de datos, pero ya no compite con la categoría en la vista principal."""

    def test_la_vista_principal_no_muestra_el_indice_hen(self):
        from test_app_humo import ejecutar
        for seccion in ("Explorar rutas", "Comparar alternativas"):
            t = ejecutar(seccion).textos() + ejecutar(seccion).html()
            self.assertNotIn(vr.ROTULO_INDICE, t)
            self.assertNotIn("h-eq", t)
            self.assertNotIn("Esfuerzo de referencia", t)

    def test_la_altitud_se_informa_como_aviso_y_no_forma_parte_de_la_categoria(self):
        from test_app_humo import ejecutar
        t = ejecutar(valores={"ruta_detalle": "R001"}).textos()
        self.assertIn("4 679 m", t)
        self.assertIn("El nivel Fácil, Moderada o Difícil describe el esfuerzo de caminar", t)
        self.assertNotIn("índice de esfuerzo", t)


if __name__ == "__main__":
    unittest.main()
