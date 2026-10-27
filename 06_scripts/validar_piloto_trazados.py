"""Valida conjuntamente los cuatro trazados piloto y genera su resumen."""

from pathlib import Path
import csv
import os
import sys

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd


def localizar_proyecto() -> Path:
    actual = Path.cwd().resolve()
    for candidato in (actual, actual.parent):
        if (candidato / "01_documentacion").exists():
            return candidato
    raise FileNotFoundError("No se encontro la carpeta principal del proyecto")


proyecto = localizar_proyecto()
carpeta_trazados = proyecto / "03_datos_intermedios" / "trazados"
archivo_salida = (
    proyecto / "07_resultados" / "tablas" / "resumen_piloto_trazados.csv"
)

rutas = [
    {
        "id_ruta": "R001",
        "nombre_ruta": "Sendero Cumbre Rucu Pichincha",
        "archivo": "R001_trazado_subida_cumbre_2026-10-05.geojson",
        "calidad_preliminar": "apta",
        "observacion_calidad": "Trazado corregido y continuo hasta el nodo OSM de la cumbre",
    },
    {
        "id_ruta": "R003",
        "nombre_ruta": "Sendero Cascada Condor Machay",
        "archivo": "R003_trazado_ida_continuo_2026-10-01.geojson",
        "calidad_preliminar": "apta",
        "observacion_calidad": "Trazado continuo desde el parqueadero hasta la cascada",
    },
    {
        "id_ruta": "R005",
        "nombre_ruta": "Sendero Tarabita - Cascada Nambillo",
        "archivo": "R005_trazado_preliminar_2026-10-01.geojson",
        "calidad_preliminar": "dudosa",
        "observacion_calidad": "Separacion de 106.5 m respecto al punto OSM de la cascada",
    },
    {
        "id_ruta": "R006",
        "nombre_ruta": "Sendero al Ilaló",
        "archivo": "R006_trazado_ida_continuo_2026-10-05.geojson",
        "calidad_preliminar": "apta",
        "observacion_calidad": "Subtramo continuo entre el inicio registrado y la cima",
    },
]

campos = [
    "id_ruta",
    "nombre_ruta",
    "archivo_intermedio",
    "tipo_geometria",
    "crs",
    "geometria_valida",
    "distancia_ida_km",
    "distancia_ida_vuelta_km",
    "calidad_preliminar",
    "observacion_calidad",
]

resumen = []
for ruta in rutas:
    archivo = carpeta_trazados / ruta["archivo"]
    datos = gpd.read_file(archivo)
    assert len(datos) == 1, f"{ruta['id_ruta']}: se esperaba una geometria"
    geometria = datos.geometry.iloc[0]
    assert datos.crs.to_epsg() == 4326, f"{ruta['id_ruta']}: CRS inesperado"
    assert geometria.geom_type == "LineString", f"{ruta['id_ruta']}: tipo inesperado"
    assert geometria.is_valid and not geometria.is_empty

    distancia_ida = float(datos.to_crs(32717).length.iloc[0] / 1000)
    resumen.append(
        {
            "id_ruta": ruta["id_ruta"],
            "nombre_ruta": ruta["nombre_ruta"],
            "archivo_intermedio": ruta["archivo"],
            "tipo_geometria": geometria.geom_type,
            "crs": "EPSG:4326",
            "geometria_valida": "si",
            "distancia_ida_km": f"{distancia_ida:.3f}",
            "distancia_ida_vuelta_km": f"{distancia_ida * 2:.3f}",
            "calidad_preliminar": ruta["calidad_preliminar"],
            "observacion_calidad": ruta["observacion_calidad"],
        }
    )

archivo_salida.parent.mkdir(parents=True, exist_ok=True)
with archivo_salida.open("w", encoding="utf-8", newline="") as salida:
    escritor = csv.DictWriter(salida, fieldnames=campos)
    escritor.writeheader()
    escritor.writerows(resumen)

print("Rutas piloto validadas:", len(resumen))
print("Geometrias validas:", sum(r["geometria_valida"] == "si" for r in resumen))
print(
    "Calidad preliminar:",
    {estado: sum(r["calidad_preliminar"] == estado for r in resumen) for estado in ("apta", "dudosa")},
)
print("Resumen guardado:", archivo_salida.name)
