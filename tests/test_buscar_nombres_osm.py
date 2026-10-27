import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "06_scripts"))
import buscar_nombres_osm as b  # noqa: E402


class BuscarNombres(unittest.TestCase):
    def test_consulta_acotada_a_pichincha(self):
        q = b.consulta("Coturco")
        self.assertIn('["name"~"Coturco",i]', q)
        self.assertIn("-0.58,-79.2,0.27,-77.85", q)

    def test_filas_usa_centro_y_fecha(self):
        datos = {"osm3s": {"timestamp_osm_base": "2026-07-15T00:00:00Z"}, "elements": [
            {"type": "way", "id": 5, "center": {"lat": 0.1, "lon": -78.2}, "tags": {"name": "Cerro X"}}]}
        f = b.filas("X", datos)
        self.assertEqual((f[0]["lat"], f[0]["lon"], f[0]["fecha_datos_osm"][:4]), (0.1, -78.2, "2026"))


if __name__ == "__main__":
    unittest.main()
