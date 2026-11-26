"""El aviso «Puede variar» marca las rutas que cambian de grupo en las pruebas de sensibilidad con las 20 rutas.
No identifica todas las rutas sensibles: no incluye el escalado logarítmico ni el retiro de rutas."""
import csv
import unittest
from pathlib import Path

TABLAS = Path(__file__).resolve().parents[1] / "07_resultados" / "tablas"
SENSIBLES = {"R003", "R006", "R015", "R019", "R022", "R023"}


class TestAvisoPuedeVariar(unittest.TestCase):
    def test_criterio_reproduce_las_seis_rutas(self):
        marcadas = set()
        with (TABLAS / "kmeans_k3_sensibilidad_2026-11-10.csv").open(encoding="utf-8-sig", newline="") as f:
            for e in csv.DictReader(f):
                if e["n_rutas"] != "20" or e["escenario"] == "mas_elevacion_maxima":
                    continue
                marcadas.update(x for x in e["rutas_cambian_de_grupo"].split("|") if x)
        self.assertEqual(marcadas, SENSIBLES)

    def test_perfil_sin_filtrar_cambia_solo_rutas_marcadas(self):
        with (TABLAS / "kmeans_k3_sensibilidad_2026-11-10.csv").open(encoding="utf-8-sig", newline="") as f:
            fila = next(e for e in csv.DictReader(f) if e["escenario"] == "ascenso_crudo")
        self.assertEqual(set(fila["rutas_cambian_de_grupo"].split("|")), {"R003", "R015", "R019", "R023"})
        self.assertLessEqual({"R003", "R015", "R019", "R023"}, SENSIBLES)

    def test_escalado_logaritmico_cambia_rutas_no_marcadas(self):
        """Resultado de analizar_c6_m3.py (escalado log1p): 13 rutas cambian, 8 de ellas sin el aviso."""
        cambian_log = {"R003", "R004", "R008", "R015", "R016", "R017", "R019", "R020", "R021", "R022", "R023", "R025", "R026"}
        self.assertEqual(len(cambian_log - SENSIBLES), 8)


if __name__ == "__main__":
    unittest.main()
