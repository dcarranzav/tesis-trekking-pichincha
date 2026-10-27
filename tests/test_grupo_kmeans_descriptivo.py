"""El resultado K-means se muestra solo como agrupamiento descriptivo."""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "06_scripts"))
import vista_rutas as vr


class GrupoKmeansDescriptivo(unittest.TestCase):
    def test_corte_actual(self):
        catalogo = vr.cargar_catalogo()
        alto = vr.grupo_kmeans_descriptivo("R001", catalogo)
        menor = vr.grupo_kmeans_descriptivo("R004", catalogo)
        sensible = vr.grupo_kmeans_descriptivo("R020", catalogo)
        self.assertEqual((alto["tamano"], alto["total"]), (8, 20))
        self.assertEqual((menor["tamano"], menor["total"]), (12, 20))
        self.assertIn("exigencia física", alto["descripcion"])
        self.assertTrue(sensible["sensible"])
        self.assertFalse(alto["sensible"])

    def test_rechaza_asignaciones_obsoletas(self):
        with tempfile.TemporaryDirectory() as temporal:
            archivo = Path(temporal) / "asignaciones.csv"
            with archivo.open("w", encoding="utf-8", newline="") as salida:
                escritor = csv.DictWriter(salida, fieldnames=["id_ruta", "grupo_relativo_k2", "sensible_a_parametros"])
                escritor.writeheader()
                escritor.writerow({"id_ruta": "R001", "grupo_relativo_k2": "1", "sensible_a_parametros": "no"})
            with self.assertRaises(ValueError):
                vr.grupo_kmeans_descriptivo("R001", archivo=archivo)


if __name__ == "__main__":
    unittest.main()
