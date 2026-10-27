"""Pruebas de la capa de datos de la interfaz (solo biblioteca estándar)."""

import csv
import hashlib
import json
import math
import re
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "06_scripts"))

import vista_rutas as vr  # noqa: E402

CATALOGO = vr.cargar_catalogo()
DESTINOS = vr.cargar_destinos()
ELEGIBLES = [f for f in CATALOGO if f["estado_modelado"] == vr.ELEGIBLE]
PALABRAS_PROHIBIDAS = re.compile(r"f[aá]cil|dif[ií]cil|moderad|recomend|peligro|segur[oa]\b", re.IGNORECASE)


def distancia_a_segmento(p, a, b):
    lat0 = math.radians(p[0])
    def xy(q):
        return ((q[1] - p[1]) * 111320 * math.cos(lat0), (q[0] - p[0]) * 110574)
    (x1, y1), (x2, y2) = xy(a), xy(b)
    dx, dy = x2 - x1, y2 - y1
    largo2 = dx * dx + dy * dy
    s = 0.0 if largo2 == 0 else max(0.0, min(1.0, -(x1 * dx + y1 * dy) / largo2))
    return math.hypot(x1 + s * dx, y1 + s * dy)


def metros(a, b):
    lat0 = math.radians((a[0] + b[0]) / 2)
    return math.hypot((b[1] - a[1]) * 111320 * math.cos(lat0), (b[0] - a[0]) * 110574)


def todas_las_comparaciones():
    """Cada (lugar, destino exacto) con sus alternativas, tal como las ve la página."""
    for l in vr.lugares(CATALOGO, DESTINOS):
        for d in vr.destinos_de_lugar(CATALOGO, l["lugar"], DESTINOS):
            yield l["lugar"], d["destino"], vr.alternativas_de_destino(CATALOGO, l["lugar"], d["destino"], DESTINOS)


class DestinosExactos(unittest.TestCase):
    def test_solo_aparecen_rutas_elegibles_y_sin_duplicados(self):
        ids = []
        for _, _, alternativas in todas_las_comparaciones():
            self.assertTrue(all(a["estado_modelado"] == vr.ELEGIBLE for a in alternativas))
            ids += [a["id_ruta"] for a in alternativas]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(sorted(ids), sorted(f["id_ruta"] for f in ELEGIBLES))

    def test_nunca_se_comparan_destinos_finales_distintos(self):
        for lugar, destino, alternativas in todas_las_comparaciones():
            self.assertEqual({a["destino_exacto"] for a in alternativas}, {destino})
            vr.validar_comparacion(alternativas)  # no debe lanzar
        mezcla = vr.alternativas_de_destino(CATALOGO, "Cerro Ilaló", "Cima del Cerro Ilaló", DESTINOS) + \
            vr.alternativas_de_destino(CATALOGO, "Cerro Ilaló", "Cruz del Ilaló", DESTINOS)
        with self.assertRaises(ValueError):
            vr.validar_comparacion(mezcla)

    def test_cima_y_cruz_del_ilalo_son_destinos_separados(self):
        destinos = {d["destino"]: d["n_alternativas"] for d in vr.destinos_de_lugar(CATALOGO, "Cerro Ilaló", DESTINOS)}
        self.assertEqual(destinos, {"Cima del Cerro Ilaló": 1, "Cruz del Ilaló": 1})
        cima = vr.alternativas_de_destino(CATALOGO, "Cerro Ilaló", "Cima del Cerro Ilaló", DESTINOS)
        cruz = vr.alternativas_de_destino(CATALOGO, "Cerro Ilaló", "Cruz del Ilaló", DESTINOS)
        self.assertEqual([a["id_ruta"] for a in cima], ["R006"])
        self.assertEqual([a["id_ruta"] for a in cruz], ["R022"])
        for _, _, alternativas in todas_las_comparaciones():
            self.assertFalse({"R006", "R022"} <= {a["id_ruta"] for a in alternativas})

    def test_toda_ruta_elegible_tiene_destino_exacto_definido(self):
        definidas = {d["id_ruta"] for d in DESTINOS}
        self.assertTrue({f["id_ruta"] for f in ELEGIBLES} <= definidas)

    def test_alternativas_de_un_destino_llegan_al_mismo_punto(self):
        """Control con datos reales: las llegadas de un mismo destino coinciden (< 100 m)."""
        for lugar, destino, alternativas in todas_las_comparaciones():
            finales = []
            for a in alternativas:
                perfil = vr.cargar_perfil(a["id_ruta"])
                if a["tipo_recorrido"] != "circular":
                    finales.append((perfil[-1]["lat"], perfil[-1]["lon"]))
            for x in finales[1:]:
                self.assertLess(metros(finales[0], x), 100, f"{lugar}/{destino}")

    def test_destinos_distintos_de_un_lugar_no_comparten_llegada(self):
        for l in vr.lugares(CATALOGO, DESTINOS):
            por_destino = {}
            for d in vr.destinos_de_lugar(CATALOGO, l["lugar"], DESTINOS):
                a = vr.alternativas_de_destino(CATALOGO, l["lugar"], d["destino"], DESTINOS)[0]
                if a["tipo_recorrido"] == "circular":
                    continue
                p = vr.cargar_perfil(a["id_ruta"])
                por_destino[d["destino"]] = (p[-1]["lat"], p[-1]["lon"])
            nombres = list(por_destino)
            for i, x in enumerate(nombres):
                for y in nombres[i + 1:]:
                    self.assertGreater(metros(por_destino[x], por_destino[y]), 100, f"{x} vs {y}")

    def test_mindo_se_separa_en_tres_destinos(self):
        d = {x["destino"]: x["n_alternativas"] for x in vr.destinos_de_lugar(CATALOGO, "Mindo", DESTINOS)}
        self.assertEqual(d, {"Cascada Corazón (Mindo Hermit Trail)": 1, "Mirador (Mindo Hermit Trail)": 1, "Yellow House": 3})
        yh = vr.alternativas_de_destino(CATALOGO, "Mindo", "Yellow House", DESTINOS)
        self.assertEqual([a["id_ruta"] for a in yh], ["R017", "R020", "R021"])
        self.assertTrue(vr.hay_comparacion(yh))

    def test_destino_con_una_sola_alternativa_no_finge_comparacion(self):
        unica = vr.alternativas_de_destino(CATALOGO, "Reserva Maquipucuna", "Cascada de Maquipucuna", DESTINOS)
        self.assertEqual([a["id_ruta"] for a in unica], ["R018"])
        self.assertFalse(vr.hay_comparacion(unica))

    def test_sendero_del_viento_se_muestra_sin_fingir_alternativas(self):
        unica = vr.alternativas_de_destino(
            CATALOGO, "Pululahua - Moraspungo", "Sector recreativo del Sendero del Viento", DESTINOS
        )
        self.assertEqual([a["id_ruta"] for a in unica], ["R027"])
        self.assertFalse(vr.hay_comparacion(unica))
        self.assertTrue(any("mirador" in aviso.lower() for aviso in vr.advertencias("R027")))

    def test_ruta_sin_destino_definido_queda_sola(self):
        sin = [d for d in DESTINOS if d["id_ruta"] != "R017"]
        yh = [a for a in vr.alternativas_de_destino(CATALOGO, "Mindo", "Yellow House", sin)]
        self.assertEqual([a["id_ruta"] for a in yh], ["R020", "R021"])
        solos = [d for d in vr.destinos_de_lugar(CATALOGO, "Mindo", sin) if "por definir" in d["destino"]]
        self.assertEqual(len(solos), 1)

    def test_lugar_o_destino_inexistente_o_sin_elegibles_devuelve_lista_vacia(self):
        self.assertEqual(vr.destinos_de_lugar(CATALOGO, "Lugar inventado", DESTINOS), [])
        self.assertEqual(vr.alternativas_de_destino(CATALOGO, "Mindo", "Destino inventado", DESTINOS), [])
        self.assertFalse(vr.hay_comparacion([]))
        sin_elegibles = [dict(f, estado_modelado="no_elegible_aun") for f in CATALOGO]
        self.assertEqual(vr.lugares(sin_elegibles, DESTINOS), [])
        self.assertEqual(vr.destinos_de_lugar(sin_elegibles, "Mindo", DESTINOS), [])

    def test_rutas_no_elegibles_nunca_se_listan(self):
        mostradas = {a["id_ruta"] for _, _, alts in todas_las_comparaciones() for a in alts}
        for excluida in ("R002", "R005", "R007", "R009", "R010", "R012", "R014"):
            self.assertNotIn(excluida, mostradas)

    def test_no_se_dibujan_accesos_inexistentes_de_ilalo(self):
        textos = " ".join(a["nombre_variante"] for _, _, alts in todas_las_comparaciones()
                          for a in alts if a["id_ruta"] in ("R006", "R022"))
        self.assertNotIn("Merced", textos)
        self.assertNotIn("Cumbayá", textos)
        self.assertTrue(any("La Merced" in n for n in vr.notas_de_lugar("Cerro Ilaló")))


class EstadosYTextos(unittest.TestCase):
    def test_r001_muestra_aviso_destacado_de_alta_montana_t3_y_criterios(self):
        avisos = vr.advertencias_destacadas("R001")
        self.assertEqual(len(avisos), 1)
        for frase in ("Alta montaña", "T3", "según I10/E10", "clase física es relativa"):
            self.assertIn(frase, avisos[0])
        self.assertEqual(vr.advertencias_destacadas("R003"), [])
        self.assertIn(avisos[0], vr.advertencias("R001"))
        self.assertIsNone(PALABRAS_PROHIBIDAS.search(avisos[0]))

    def test_tres_estados_distintos(self):
        c = vr.conteo_estados(CATALOGO)
        self.assertEqual((c["procesadas"], c["elegibles_provisionales"], c["habilitadas_recomendacion"]), (27, 20, 0))
        self.assertEqual(c["no_elegibles"], 7)

    def test_ningun_texto_de_la_interfaz_llama_verificada_a_una_ruta_provisional(self):
        fuentes = [RAIZ / "app.py", RAIZ / "06_scripts" / "vista_rutas.py"]
        for f in fuentes:
            for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if "verificad" in linea.lower() and "registro" not in linea:
                    self.fail(f"{f.name}:{n} usa «verificad…»: {linea.strip()}")
        for aviso in vr.advertencias("R003"):
            self.assertNotRegex(aviso, r"verificad[ao]s?\b(?!.*no confirma)")


class ClasificacionEnDesarrollo(unittest.TestCase):
    def test_sin_modelo_final_la_clasificacion_no_esta_disponible(self):
        estado = vr.estado_clasificacion(CATALOGO)
        self.assertFalse(estado["disponible"])
        self.assertEqual((estado["elegibles"], estado["meta"], estado["faltan"]), (len(ELEGIBLES), 20, 20 - len(ELEGIBLES)))
        self.assertIn("en desarrollo", estado["mensaje"])
        self.assertIsNone(PALABRAS_PROHIBIDAS.search(estado["mensaje"]))
        self.assertFalse(vr.NIVELES_FINALES.exists(), "no debe existir un archivo de niveles finales")

    def test_un_archivo_de_niveles_parcial_no_basta_aunque_haya_20_rutas(self):
        with tempfile.TemporaryDirectory() as tmp:
            falso = Path(tmp) / "niveles.csv"
            falso.write_text("id_ruta,nivel\nR003,1\n", encoding="utf-8")
            self.assertFalse(vr.estado_clasificacion(CATALOGO, falso)["disponible"])

    def test_muestra_completa_sin_archivo_final_sigue_en_desarrollo(self):
        veinte = [dict(f, estado_modelado=vr.ELEGIBLE) for f in (CATALOGO * 2)[:20]]
        with tempfile.TemporaryDirectory() as tmp:
            estado = vr.estado_clasificacion(veinte, Path(tmp) / "no_existe.csv")
        self.assertFalse(estado["disponible"])
        self.assertIn("en desarrollo", estado["mensaje"])

    def _registro(self, tmp, niveles_texto, **cambios):
        niveles = Path(tmp) / "niveles.csv"
        niveles.write_text(niveles_texto, encoding="utf-8")
        registro = {
            "aprobado": True, "aprobado_por": "Tutor de tesis", "fecha": "2026-10-21",
            "version_modelo": "k-means-v1", "n_rutas_elegibles": 20,
            "sha256_niveles": hashlib.sha256(niveles.read_bytes()).hexdigest(),
        }
        registro.update(cambios)
        validacion = Path(tmp) / "validacion.json"
        validacion.write_text(json.dumps(registro), encoding="utf-8")
        return niveles, validacion

    def test_veinte_rutas_y_un_csv_no_bastan_sin_validacion_explicita(self):
        veinte = [dict(f, id_ruta=f"R{n:03d}", estado_modelado=vr.ELEGIBLE) for n, f in enumerate((CATALOGO * 2)[:20], 100)]
        texto = "id_ruta,nivel\n" + "".join(f"{f['id_ruta']},1\n" for f in veinte)
        with tempfile.TemporaryDirectory() as tmp:
            niveles = Path(tmp) / "niveles.csv"
            niveles.write_text(texto, encoding="utf-8")
            estado = vr.estado_clasificacion(veinte, niveles, 20, Path(tmp) / "no_existe.json")
            self.assertFalse(estado["disponible"])
            self.assertIn("validación explícita", estado["mensaje"])

    def test_validacion_explicita_valida_habilita_la_clasificacion(self):
        veinte = [dict(f, id_ruta=f"R{n:03d}", estado_modelado=vr.ELEGIBLE) for n, f in enumerate((CATALOGO * 2)[:20], 100)]
        texto = "id_ruta,nivel\n" + "".join(f"{f['id_ruta']},1\n" for f in veinte)
        with tempfile.TemporaryDirectory() as tmp:
            niveles, validacion = self._registro(tmp, texto)
            self.assertTrue(vr.estado_clasificacion(veinte, niveles, 20, validacion)["disponible"])

    def test_validacion_invalida_no_habilita(self):
        veinte = [dict(f, id_ruta=f"R{n:03d}", estado_modelado=vr.ELEGIBLE) for n, f in enumerate((CATALOGO * 2)[:20], 100)]
        texto = "id_ruta,nivel\n" + "".join(f"{f['id_ruta']},1\n" for f in veinte)
        casos = [
            {"aprobado": False}, {"aprobado_por": ""}, {"version_modelo": " "}, {"fecha": "2999-01-01"},
            {"fecha": "no-es-fecha"}, {"n_rutas_elegibles": 19}, {"sha256_niveles": "0" * 64},
        ]
        for cambio in casos:
            with tempfile.TemporaryDirectory() as tmp:
                niveles, validacion = self._registro(tmp, texto, **cambio)
                self.assertFalse(vr.estado_clasificacion(veinte, niveles, 20, validacion)["disponible"], cambio)
        with tempfile.TemporaryDirectory() as tmp:  # el archivo cambia después de aprobarse
            niveles, validacion = self._registro(tmp, texto)
            niveles.write_text(texto + "R999,2\n", encoding="utf-8")
            self.assertFalse(vr.estado_clasificacion(veinte, niveles, 20, validacion)["disponible"])
        with tempfile.TemporaryDirectory() as tmp:  # niveles que no cubren las rutas elegibles
            niveles, validacion = self._registro(tmp, "id_ruta,nivel\nR100,1\n")
            self.assertFalse(vr.estado_clasificacion(veinte, niveles, 20, validacion)["disponible"])

    def test_la_validacion_real_no_existe_todavia(self):
        self.assertFalse(vr.VALIDACION_MODELO.exists())
        self.assertFalse(vr.estado_clasificacion(CATALOGO)["disponible"])

    def test_la_recomendacion_real_sigue_bloqueada(self):
        try:
            import pandas as pd
            import logica_recomendacion as lr
        except ImportError:
            self.skipTest("pandas no está instalado en este entorno")
        dataset = pd.read_csv(vr.TABLA, encoding="utf-8-sig")
        mindo = lr.alternativas_por_destino(dataset, "D010", destino_exacto="Yellow House")
        with self.assertRaises(lr.ModeloNoValidado):
            lr.recomendar(mindo, lr.Preferencias(nivel_deseado=1), None, version_modelo_final=None)
        niveles_inventados = {r: 1 for r in mindo["id_ruta"]}
        with self.assertRaises(lr.ModeloNoValidado):
            lr.recomendar(mindo, lr.Preferencias(nivel_deseado=1), niveles_inventados, version_modelo_final="x")

    def test_los_datos_mostrados_no_contienen_campos_de_nivel(self):
        for f in vr.alternativas_de_destino(CATALOGO, "Mindo", "Yellow House", DESTINOS):
            for clave in f:
                self.assertNotRegex(clave, r"nivel|dificultad|cluster|grupo_")


class PerfilesYTrayectos(unittest.TestCase):
    def test_perfil_coincide_con_dataset_y_geojson_en_todas_las_elegibles(self):
        for f in ELEGIBLES:
            with self.subTest(ruta=f["id_ruta"]):
                perfil = vr.cargar_perfil(f["id_ruta"])
                self.assertAlmostEqual(perfil[-1]["d"], float(f["distancia_trazado_km"]) * 1000, delta=2)
                _, linea = vr.cargar_trazado(f["id_ruta"])
                for p in perfil:
                    desviacion = min(distancia_a_segmento((p["lat"], p["lon"]), a, b) for a, b in zip(linea, linea[1:]))
                    self.assertLess(desviacion, 1.0, "punto del perfil fuera de la línea del GeoJSON")
                self.assertEqual((perfil[0]["lat"], perfil[0]["lon"]), linea[0])
                self.assertEqual((perfil[-1]["lat"], perfil[-1]["lon"]), linea[-1])

    def test_ida_y_vuelta_regresa_exactamente_al_inicio_y_duplica_la_distancia(self):
        for f in ELEGIBLES:
            if f["tipo_recorrido"] == "circular":
                continue
            with self.subTest(ruta=f["id_ruta"]):
                t = vr.trayecto_simulado(vr.cargar_perfil(f["id_ruta"]), f["tipo_recorrido"])
                p = t["puntos"]
                self.assertEqual((p[0]["lat"], p[0]["lon"]), (p[-1]["lat"], p[-1]["lon"]))
                self.assertAlmostEqual(t["total_m"], float(f["distancia_total_km"]) * 1000, delta=3)
                self.assertTrue(all(b["d"] > a["d"] for a, b in zip(p, p[1:])))

    def test_pendiente_del_regreso_invierte_el_signo_de_la_ida(self):
        perfil = vr.cargar_perfil("R003")
        p = vr.trayecto_simulado(perfil, "ida_y_vuelta")["puntos"]
        n = len(perfil)
        for k in (1, 10, 50):
            idx_ida = n - 1 - k  # el punto k del regreso es el índice n-1-k de la ida
            self.assertAlmostEqual(p[n - 1 + k]["pend"], -perfil[idx_ida + 1]["pend"])
            self.assertAlmostEqual(p[n - 1 + k]["elev"], perfil[idx_ida]["elev"])

    def test_circuito_cierra_y_no_agrega_regreso(self):
        f = next(r for r in ELEGIBLES if r["tipo_recorrido"] == "circular")
        t = vr.trayecto_simulado(vr.cargar_perfil(f["id_ruta"]), "circular")
        self.assertIsNone(t["giro"])
        self.assertTrue(t["circular"])
        p = t["puntos"]
        self.assertLess(metros((p[0]["lat"], p[0]["lon"]), (p[-1]["lat"], p[-1]["lon"])), 5)
        self.assertAlmostEqual(t["total_m"], float(f["distancia_total_km"]) * 1000, delta=3)

    def test_clases_de_pendiente(self):
        self.assertEqual([vr.clase_pendiente(x) for x in (0, 9.9, 10, 25, 30, 99)], [0, 0, 1, 2, 3, 3])

    def test_perfil_invalido_se_rechaza(self):
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp)
            (carpeta / "R999_perfil_elevacion_procesado_2026-10-21.csv").write_text(
                "id_ruta,orden,distancia_m,longitud,latitud,elevacion_m,fuente_elevacion,elevacion_mediana3_m,cambio_elevacion_m,pendiente_pct,metodo_filtrado\n"
                "R999,0,0,-78.4,-0.2,2500,x,2500,,,m\nR999,1,0,-78.4,-0.2,2500,x,2500,0,0,m\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                vr.cargar_perfil("R999", carpeta)
            with self.assertRaises(FileNotFoundError):
                vr.cargar_perfil("R998", carpeta)
        with self.assertRaises(ValueError):
            vr.ruta_perfil("../etc/passwd")


class AccesosYAvisos(unittest.TestCase):
    def test_nombre_de_acceso_de_r006_no_se_presenta_como_verificado(self):
        fila = next(f for f in ELEGIBLES if f["id_ruta"] == "R006")
        perfil = vr.cargar_perfil("R006")
        inicio = (perfil[0]["lat"], perfil[0]["lon"])
        acceso = vr.verificar_acceso(fila, inicio)
        self.assertEqual(acceso["estado"], "por_verificar")
        self.assertTrue(acceso["etiqueta"].startswith("Acceso por verificar"))
        self.assertIn("-0.2440", acceso["etiqueta"])
        self.assertNotIn("El Tingo", acceso["etiqueta"])
        self.assertIn("no se renombra", acceso["nota"])

    def test_la_distancia_citada_entre_inicios_de_r006_y_r022_es_correcta(self):
        i6 = vr.cargar_perfil("R006")[0]
        i22 = vr.cargar_perfil("R022")[0]
        d = metros((i6["lat"], i6["lon"]), (i22["lat"], i22["lon"]))
        self.assertAlmostEqual(d / 1000, 4.5, delta=0.1)
        self.assertGreater(i6["lat"], i22["lat"], "R006 debe iniciar al norte de R022")

    def test_rutas_sin_observacion_usan_el_nombre_de_la_fuente(self):
        fila = next(f for f in ELEGIBLES if f["id_ruta"] == "R015")
        acceso = vr.verificar_acceso(fila, (0, 0))
        self.assertEqual(acceso["etiqueta"], fila["nombre_variante"])

    def test_todas_las_rutas_llevan_el_aviso_de_elegibilidad_provisional(self):
        for f in ELEGIBLES:
            self.assertIn("provisional", vr.advertencias(f["id_ruta"])[0].lower())

    def test_avisos_conocidos_y_solapamientos(self):
        self.assertTrue(any("vados" in a for a in vr.advertencias("R022")))
        self.assertTrue(any("R017" in a for a in vr.advertencias("R020")))
        self.assertFalse(any("Comparte parte" in a for a in vr.advertencias("R003")))

    def test_archivo_de_verificacion_solo_cita_rutas_o_lugares_existentes(self):
        ids = {f["id_ruta"] for f in CATALOGO}
        lugares = {l["lugar"] for l in vr.lugares(CATALOGO, DESTINOS)}
        for r in vr.cargar_verificacion():
            self.assertTrue(r["clave"] in ids or r["clave"] in lugares, r["clave"])
            self.assertTrue(r["fuente_documento"].strip())

    def test_alias_de_sesion_se_limpia(self):
        self.assertEqual(vr.limpiar_alias("  <b>Ana_María</b> **x**  "), "bAna Maríab x")
        self.assertEqual(vr.limpiar_alias(None), "")
        self.assertEqual(len(vr.limpiar_alias("a" * 100)), 40)
        self.assertNotIn("<", vr.limpiar_alias("<script>alert(1)</script>"))


class VisorYDescargas(unittest.TestCase):
    def test_visor_se_construye_para_todas_las_elegibles_con_atribuciones(self):
        for f in ELEGIBLES:
            with self.subTest(ruta=f["id_ruta"]):
                html = vr.construir_visor_html(vr.datos_visor(f["id_ruta"], f))
                self.assertIn("OpenStreetMap", html)
                self.assertIn("Copernicus", html)
                self.assertNotIn("__DATOS__", html)
                self.assertNotIn("__LEAFLET", html)
                self.assertLess(len(html), 1_000_000)
                self.assertIsNone(PALABRAS_PROHIBIDAS.search(re.sub(r"<style>.*?</style>|<script>.*?</script>", "", html, flags=re.S)))

    def test_datos_del_visor_son_json_coherente(self):
        f = next(r for r in ELEGIBLES if r["id_ruta"] == "R017")
        d = vr.datos_visor("R017", f)
        n = len(d["d"])
        self.assertTrue(all(len(d[k]) == n for k in ("lat", "lon", "elev", "pend")))
        self.assertEqual((d["lat"][0], d["lon"][0]), (d["lat"][-1], d["lon"][-1]))
        self.assertEqual(d["titulo"], f["nombre_ruta"])
        self.assertNotIn("R017", d["titulo"])
        json.dumps(d)

    def test_nombres_con_codigo_no_rompen_la_pagina(self):
        f = dict(next(r for r in ELEGIBLES if r["id_ruta"] == "R003"), nombre_ruta="</script><script>alert(1)</script>")
        html = vr.construir_visor_html(vr.datos_visor("R003", f))
        self.assertNotIn("alert(1)</script>", html)
        self.assertNotIn("<script>alert", html)
        self.assertEqual(html.count("</script>"), html.count("<script>"))

    def test_gpx_no_inventa_elevaciones_ni_tiempos(self):
        gpx = vr.gpx_ida("R003", "Prueba").decode("utf-8")
        self.assertIn("<trkpt", gpx)
        self.assertNotIn("<ele", gpx)
        self.assertNotIn("<time", gpx)
        _, puntos = vr.cargar_trazado("R003")
        self.assertEqual(gpx.count("<trkpt"), len(puntos))


if __name__ == "__main__":
    unittest.main()
