"""Protege la construcción de la variante OSM Senderos 1 y 2."""

import importlib.util
from pathlib import Path
import unittest

from pyproj import Transformer
from shapely.geometry import LineString
from shapely.ops import transform


ARCHIVO = Path(__file__).resolve().parents[1] / "06_scripts/procesar_r021_yellow_house.py"
spec = importlib.util.spec_from_file_location("procesar_r021_yellow_house", ARCHIVO)
modulo = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(modulo)


class VarianteSenderosUnoDosTests(unittest.TestCase):
    def test_mismos_extremos_y_desvios_reales(self):
        vias = modulo.cargar_vias()
        linea, uniones = modulo.construir(vias)
        principal = modulo.coordenadas(vias[modulo.VIA_PRINCIPAL])
        self.assertTrue(linea.is_valid and linea.is_simple)
        self.assertEqual(linea.coords[0], principal[0])
        self.assertEqual(linea.coords[-1], principal[-1])
        self.assertEqual(set(uniones), set(modulo.DESVIOS))
        for id_via, nodos in uniones.items():
            self.assertEqual(set(nodos), set(vias[id_via]["nodes"]) & set(vias[modulo.VIA_PRINCIPAL]["nodes"]))

    def test_diferencia_espacial_frente_a_principal(self):
        vias = modulo.cargar_vias()
        linea, _ = modulo.construir(vias)
        proyeccion = Transformer.from_crs(4326, 32717, always_xy=True).transform
        variante = transform(proyeccion, linea)
        principal = transform(
            proyeccion,
            LineString(modulo.coordenadas(vias[modulo.VIA_PRINCIPAL])),
        )
        self.assertLess(principal.intersection(variante.buffer(20)).length / principal.length, 0.90)
        self.assertLess(variante.intersection(principal.buffer(20)).length / variante.length, 0.90)


if __name__ == "__main__":
    unittest.main()
