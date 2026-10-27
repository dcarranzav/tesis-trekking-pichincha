"""Pruebas de comparación y de bloqueo de recomendaciones prematuras."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

import pandas as pd


ARCHIVO = Path(__file__).resolve().parents[1] / "06_scripts/logica_recomendacion.py"
especificacion = importlib.util.spec_from_file_location("logica_recomendacion", ARCHIVO)
modulo = importlib.util.module_from_spec(especificacion)
assert especificacion.loader is not None
import sys
sys.modules[especificacion.name] = modulo
especificacion.loader.exec_module(modulo)


def datos_prueba():
    return pd.DataFrame(
        [
            {"id_ruta": "T1", "id_destino": "D1", "estado_modelado": "elegible_actual", "distancia_total_km": 3.0, "ascenso_total_m": 150.0, "elevacion_max_m": 2500, "pendiente_media_abs_pct": 8},
            {"id_ruta": "T2", "id_destino": "D1", "estado_modelado": "elegible_actual", "distancia_total_km": 5.0, "ascenso_total_m": 300.0, "elevacion_max_m": 2700, "pendiente_media_abs_pct": 10},
            {"id_ruta": "T3", "id_destino": "D1", "estado_modelado": "no_elegible_aun", "distancia_total_km": 2.0, "ascenso_total_m": 80.0, "elevacion_max_m": 2400, "pendiente_media_abs_pct": 6},
            {"id_ruta": "T4", "id_destino": "D2", "estado_modelado": "elegible_actual", "distancia_total_km": 1.0, "ascenso_total_m": 50.0, "elevacion_max_m": 2200, "pendiente_media_abs_pct": 5},
        ]
    )


def mapeo_prueba():
    return pd.DataFrame(
        [
            {"id_ruta": "T1", "lugar": "L1", "destino_exacto": "Cima A"},
            {"id_ruta": "T2", "lugar": "L1", "destino_exacto": "Cima A"},
            {"id_ruta": "T3", "lugar": "L1", "destino_exacto": "Cima A"},
            {"id_ruta": "T4", "lugar": "L2", "destino_exacto": "Cima B"},
        ]
    )


class LogicaRecomendacionTests(unittest.TestCase):
    def test_filtra_destino_y_elegibilidad(self):
        rutas = modulo.alternativas_por_destino(datos_prueba(), "D1", mapeo_prueba())
        self.assertEqual(rutas.id_ruta.tolist(), ["T1", "T2"])
        with self.assertRaisesRegex(ValueError, "desconocido"):
            modulo.alternativas_por_destino(datos_prueba(), "D9", mapeo_prueba())

    def test_bloquea_modelo_no_validado_y_clase_faltante(self):
        rutas = modulo.alternativas_por_destino(datos_prueba(), "D1", mapeo_prueba())
        preferencias = modulo.Preferencias(nivel_deseado=2)
        with self.assertRaises(modulo.ModeloNoValidado):
            modulo.recomendar(rutas, preferencias, None, version_modelo_final=None)
        with self.assertRaisesRegex(modulo.ModeloNoValidado, "T2"):
            modulo.recomendar(rutas, preferencias, {"T1": 1}, version_modelo_final="prueba", rutas_habilitadas={"T1", "T2"})

    def test_no_recomienda_ruta_sin_verificacion_de_acceso(self):
        rutas = modulo.alternativas_por_destino(datos_prueba(), "D1", mapeo_prueba())
        preferencias = modulo.Preferencias(nivel_deseado=1)
        niveles = {"T1": 1, "T2": 2}
        with self.assertRaisesRegex(modulo.ModeloNoValidado, "apertura"):
            modulo.recomendar(rutas, preferencias, niveles, version_modelo_final="solo_prueba")
        resultado = modulo.recomendar(
            rutas, preferencias, niveles, version_modelo_final="solo_prueba",
            rutas_habilitadas={"T1"},
        )
        self.assertEqual([fila["id_ruta"] for fila in resultado], ["T1"])

    def test_limites_y_orden_con_clases_sinteticas(self):
        rutas = modulo.alternativas_por_destino(datos_prueba(), "D1", mapeo_prueba())
        niveles = {"T1": 2, "T2": 2}
        preferencia = modulo.Preferencias(nivel_deseado=2, origen_lat_lon=(0, 0))
        inicios = {"T1": (0, 0.02), "T2": (0, 0.01)}
        orden = modulo.recomendar(
            rutas, preferencia, niveles, version_modelo_final="solo_prueba",
            inicios_lat_lon=inicios, rutas_habilitadas={"T1", "T2"},
        )
        self.assertEqual([r["id_ruta"] for r in orden], ["T2", "T1"])
        limitado = modulo.recomendar(
            rutas, modulo.Preferencias(nivel_deseado=2, distancia_max_km=4),
            niveles, version_modelo_final="solo_prueba", rutas_habilitadas={"T1", "T2"},
        )
        self.assertEqual([r["id_ruta"] for r in limitado], ["T1"])

    def test_no_inventa_cercania_si_falta_inicio(self):
        rutas = modulo.alternativas_por_destino(datos_prueba(), "D1", mapeo_prueba())
        with self.assertRaisesRegex(ValueError, "Falta inicio"):
            modulo.recomendar(
                rutas, modulo.Preferencias(nivel_deseado=1, origen_lat_lon=(0, 0)),
                {"T1": 1, "T2": 2}, version_modelo_final="solo_prueba",
                inicios_lat_lon={"T1": (0, 0)}, rutas_habilitadas={"T1", "T2"},
            )

    def test_rechaza_dataset_crudo_con_rutas_no_elegibles(self):
        with self.assertRaisesRegex(modulo.ModeloNoValidado, "fuera del conjunto elegible"):
            modulo.recomendar(
                datos_prueba().query("id_destino == 'D1'").assign(destino_exacto="Cima A"),
                modulo.Preferencias(nivel_deseado=1),
                {"T1": 1, "T2": 2, "T3": 1},
                version_modelo_final="solo_prueba",
                rutas_habilitadas={"T1", "T2", "T3"},
            )

    def test_rechaza_mezcla_de_destinos_y_ids_duplicados(self):
        rutas = datos_prueba().query("estado_modelado == 'elegible_actual'")
        with self.assertRaisesRegex(ValueError, "un solo destino"):
            modulo.recomendar(
                rutas, modulo.Preferencias(nivel_deseado=1),
                {"T1": 1, "T2": 2, "T4": 1},
                version_modelo_final="solo_prueba",
                rutas_habilitadas={"T1", "T2", "T4"},
            )
        duplicadas = pd.concat([rutas.iloc[[0]], rutas.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "duplicados"):
            modulo.recomendar(
                duplicadas, modulo.Preferencias(nivel_deseado=1),
                {"T1": 1}, version_modelo_final="solo_prueba",
                rutas_habilitadas={"T1"},
            )


DATASET_REAL = Path(__file__).resolve().parents[1] / "07_resultados/tablas/dataset_clasificacion_rutas.csv"


class DestinoExactoRealTests(unittest.TestCase):
    """Con los datos reales, un destino amplio nunca mezcla destinos finales distintos."""

    @classmethod
    def setUpClass(cls):
        cls.dataset = pd.read_csv(DATASET_REAL, encoding="utf-8-sig")
        cls.mapeo = modulo.cargar_destinos_exactos()

    def ids(self, id_destino, exacto):
        return modulo.alternativas_por_destino(self.dataset, id_destino, self.mapeo, exacto).id_ruta.tolist()

    def test_mindo_exige_elegir_destino_exacto(self):
        with self.assertRaisesRegex(ValueError, "varios destinos exactos"):
            modulo.alternativas_por_destino(self.dataset, "D010", self.mapeo)

    def test_mindo_separa_cascada_corazon_mirador_y_yellow_house(self):
        self.assertEqual(self.ids("D010", "Cascada Corazón (Mindo Hermit Trail)"), ["R015"])
        self.assertEqual(self.ids("D010", "Mirador (Mindo Hermit Trail)"), ["R016"])
        self.assertEqual(self.ids("D010", "Yellow House"), ["R017", "R020", "R021"])

    def test_pondona_separa_circuito_y_parte_alta(self):
        with self.assertRaisesRegex(ValueError, "varios destinos exactos"):
            modulo.alternativas_por_destino(self.dataset, "D004", self.mapeo)
        self.assertEqual(self.ids("D004", "Circuito Pondoña (recorrido circular)"), ["R004"])
        self.assertEqual(self.ids("D004", "Parte alta del Pondoña desde la base oriental"), ["R008"])

    def test_recomendar_rechaza_mezclar_destinos_exactos(self):
        todas = _con_exacto(self.dataset, self.mapeo)
        pruebas = [
            ("D010", ["R015", "R016", "R017"]),
            ("D010", ["R016", "R017", "R020"]),
            ("D004", ["R004", "R008"]),
        ]
        for id_destino, ids in pruebas:
            mezcla = todas.loc[todas["id_ruta"].isin(ids)]
            with self.assertRaisesRegex(ValueError, "destinos finales distintos"):
                modulo.recomendar(
                    mezcla, modulo.Preferencias(nivel_deseado=1), {r: 1 for r in ids},
                    version_modelo_final="solo_prueba", rutas_habilitadas=set(ids),
                )

    def test_recomendar_exige_columna_destino_exacto(self):
        crudo = self.dataset.loc[self.dataset["id_ruta"].isin(["R017", "R020"])]
        with self.assertRaisesRegex(ValueError, "destino_exacto"):
            modulo.recomendar(
                crudo, modulo.Preferencias(nivel_deseado=1), {"R017": 1, "R020": 1},
                version_modelo_final="solo_prueba", rutas_habilitadas={"R017", "R020"},
            )

    def test_cada_destino_amplio_real_solo_devuelve_un_destino_exacto(self):
        for id_destino in self.dataset.loc[self.dataset["estado_modelado"].eq("elegible_actual"), "id_destino"].unique():
            exactos = _con_exacto(
                self.dataset.loc[self.dataset["id_destino"].eq(id_destino) & self.dataset["estado_modelado"].eq("elegible_actual")],
                self.mapeo,
            )["destino_exacto"].unique()
            for destino in exactos:
                resultado = modulo.alternativas_por_destino(self.dataset, id_destino, self.mapeo, destino)
                self.assertEqual(resultado["destino_exacto"].nunique(), 1)

    def test_recomendacion_real_sigue_bloqueada(self):
        rutas = modulo.alternativas_por_destino(self.dataset, "D010", self.mapeo, "Yellow House")
        with self.assertRaises(modulo.ModeloNoValidado):
            modulo.recomendar(rutas, modulo.Preferencias(nivel_deseado=1), None, version_modelo_final=None)
        with self.assertRaises(modulo.ModeloNoValidado):
            modulo.recomendar(
                rutas, modulo.Preferencias(nivel_deseado=1), {r: 1 for r in rutas.id_ruta},
                version_modelo_final="x",
            )

    def test_mapeo_rechaza_ruta_duplicada(self):
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / "m.csv"
            archivo.write_text("lugar,destino_exacto,id_ruta\nA,X,R001\nA,Y,R001\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dos destinos"):
                modulo.cargar_destinos_exactos(archivo)


def _con_exacto(dataset, mapeo):
    return modulo._con_destino_exacto(dataset, mapeo)


if __name__ == "__main__":
    unittest.main()
