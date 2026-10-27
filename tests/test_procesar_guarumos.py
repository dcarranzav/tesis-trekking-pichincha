"""R026 debe proceder del XML íntegro archivado, terminar en Guarumos y coincidir con el camino más corto por nodos."""

from hashlib import sha256
import importlib.util
from pathlib import Path
import unittest


RAIZ = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("procesar_guarumos", RAIZ / "06_scripts/procesar_r026_guarumos.py")
MODULO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULO)
SPEC_A = importlib.util.spec_from_file_location("analizar_zona", RAIZ / "06_scripts/analizar_zona_osm.py")
ANALIZADOR = importlib.util.module_from_spec(SPEC_A)
SPEC_A.loader.exec_module(ANALIZADOR)


class ValidacionGuarumos(unittest.TestCase):
    def test_fuente_extremos_y_coincidencia_con_camino_minimo(self):
        self.assertEqual(sha256(MODULO.FUENTE.read_bytes()).hexdigest().upper(), MODULO.SHA_FUENTE)
        _, datos = MODULO.construir()
        refs = datos["refs"]
        self.assertEqual(refs[0], MODULO.NODO_INICIO)
        self.assertEqual(refs[-1], MODULO.NODO_DESTINO)
        self.assertIn(MODULO.NODO_BIFURCACION, refs)
        nodos, _, vias = ANALIZADOR.cargar(MODULO.FUENTE)
        g, _ = ANALIZADOR.grafo(nodos, vias)
        _, nodos_camino, _ = ANALIZADOR.camino(g, {MODULO.NODO_INICIO}, MODULO.NODO_DESTINO)
        self.assertEqual(refs, nodos_camino)
        self.assertAlmostEqual(datos["distancia_ida_km"], 1.067, delta=0.005)


if __name__ == "__main__":
    unittest.main()
