"""Controles previos a conservar la fuente de la candidata R022."""

import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


RUTA_SCRIPT = Path(__file__).resolve().parents[1] / "06_scripts/descargar_r022_ilalo.py"
SPEC = importlib.util.spec_from_file_location("descargar_r022_ilalo", RUTA_SCRIPT)
MODULO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULO)


def muestra() -> bytes:
    raiz = ET.Element("osm")
    via = ET.SubElement(raiz, "way", id="297582904")
    refs = ["1323665115"] + [str(n) for n in range(1000, 1126)] + ["1369911783"]
    for ref in refs:
        ET.SubElement(via, "nd", ref=ref)
        ET.SubElement(raiz, "node", id=ref, lat="-0.275", lon="-78.43")
    for clave, valor in (
        ("name", "camino a la Cruz del Ilaló"),
        ("highway", "path"),
        ("sac_scale", "hiking"),
    ):
        ET.SubElement(via, "tag", k=clave, v=valor)
    return ET.tostring(raiz, encoding="utf-8")


class ValidacionFuenteIlalo(unittest.TestCase):
    def test_fuente_completa(self):
        self.assertEqual(MODULO.validar(muestra()), 128)

    def test_rechaza_nombre_distinto(self):
        self.assertRaises(ValueError, MODULO.validar, muestra().replace(b"camino a la Cruz", b"otro camino"))

    def test_rechaza_nodo_sin_coordenadas(self):
        raiz = ET.fromstring(muestra())
        raiz.remove(raiz.findall("node")[-1])
        self.assertRaises(ValueError, MODULO.validar, ET.tostring(raiz))


if __name__ == "__main__":
    unittest.main()
