"""Audita de extremo a extremo la integridad del proyecto de tesis.

La auditoria cruza inventario, dataset maestro, datos originales, geometrías,
perfiles, figuras, evidencias, notebooks, scripts y dependencias declaradas.
Genera una tabla legible por máquina y un informe breve para revisión humana.
"""

from __future__ import annotations

from argparse import ArgumentParser
from datetime import date
import json
import os
from pathlib import Path
import re
import runpy
import sys

gdal_data = Path(sys.prefix) / "Library" / "share" / "gdal"
if gdal_data.exists():
    os.environ["GDAL_DATA"] = str(gdal_data)

import geopandas as gpd
import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
DOCUMENTACION = RAIZ / "01_documentacion"
ORIGINALES = RAIZ / "02_datos_originales"
INTERMEDIOS = RAIZ / "03_datos_intermedios"
PROCESADOS = RAIZ / "04_datos_procesados"
NOTEBOOKS = RAIZ / "05_notebooks"
SCRIPTS = RAIZ / "06_scripts"
RESULTADOS = RAIZ / "07_resultados"
EVIDENCIAS = RAIZ / "08_evidencias"
FECHA = ""


class Auditoria:
    def __init__(self) -> None:
        self.filas: list[dict[str, str]] = []

    def registrar(self, ambito: str, elemento: str, condicion: bool, detalle_ok: str, detalle_error: str) -> None:
        self.filas.append(
            {
                "ambito": ambito,
                "elemento": elemento,
                "estado": "OK" if condicion else "ERROR",
                "detalle": detalle_ok if condicion else detalle_error,
            }
        )

    def advertir(self, ambito: str, elemento: str, detalle: str) -> None:
        self.filas.append(
            {
                "ambito": ambito,
                "elemento": elemento,
                "estado": "ADVERTENCIA",
                "detalle": detalle,
            }
        )

    def tabla(self) -> pd.DataFrame:
        return pd.DataFrame(self.filas, columns=["ambito", "elemento", "estado", "detalle"])


def archivo_unico(patron: str) -> Path | None:
    archivos = sorted(RAIZ.glob(patron))
    return archivos[0] if len(archivos) == 1 else None


def geometria_vigente(id_ruta: str) -> Path | None:
    """Escoge la versión más reciente sin eliminar trazados históricos."""
    archivos = sorted((INTERMEDIOS / "trazados").glob(f"{id_ruta}_trazado_*.geojson"))
    if not archivos:
        return None
    fechas = {}
    for archivo in archivos:
        coincidencia = re.search(r"(\d{4}-\d{2}-\d{2})", archivo.name)
        fecha = coincidencia.group(1) if coincidencia else "0000-00-00"
        fechas.setdefault(fecha, []).append(archivo)
    vigentes = fechas[max(fechas)]
    return vigentes[0] if len(vigentes) == 1 else None


def auditar_rutas(auditoria: Auditoria, inventario: pd.DataFrame, dataset: pd.DataFrame) -> None:
    ids_inventario = set(inventario["id_ruta"])
    ids_dataset = set(dataset["id_ruta"])
    auditoria.registrar(
        "rutas",
        "concordancia_ids_inventario_dataset",
        ids_inventario == ids_dataset,
        f"{len(ids_inventario)} rutas coinciden en ambos archivos",
        f"solo_inventario={sorted(ids_inventario - ids_dataset)}; solo_dataset={sorted(ids_dataset - ids_inventario)}",
    )
    auditoria.registrar(
        "rutas",
        "ids_unicos",
        inventario["id_ruta"].is_unique and dataset["id_ruta"].is_unique,
        "Los identificadores de ruta son únicos",
        "Hay identificadores duplicados",
    )
    nombres_por_destino = inventario.groupby("id_destino")["nombre_destino"].nunique()
    destinos_ambiguos = nombres_por_destino.loc[nombres_por_destino.ne(1)].index.tolist()
    auditoria.registrar(
        "rutas",
        "nombres_destino_consistentes",
        not destinos_ambiguos,
        "Cada identificador de destino tiene un solo nombre",
        f"Destinos con nombres discordantes: {destinos_ambiguos}",
    )
    campos_sincronizados = [
        "nombre_ruta", "id_destino", "nombre_destino", "calidad_preliminar",
        "comparable_trekking", "requiere_equipo_tecnico", "decision",
    ]
    ids_comunes = ids_inventario & ids_dataset
    discordancias = [
        id_ruta
        for id_ruta in sorted(ids_comunes)
        if any(
            str(inventario.loc[inventario["id_ruta"].eq(id_ruta), campo].iloc[0])
            != str(dataset.loc[dataset["id_ruta"].eq(id_ruta), campo].iloc[0])
            for campo in campos_sincronizados
        )
    ]
    auditoria.registrar(
        "rutas",
        "inventario_dataset_metadatos_sincronizados",
        not discordancias and ids_inventario == ids_dataset,
        "Nombres, destino y decisiones coinciden entre inventario y dataset",
        f"Rutas con metadatos discordantes: {discordancias}",
    )
    elegibles = dataset.loc[dataset["estado_modelado"].eq("elegible_actual")]
    restricciones_ok = (
        elegibles["calidad_preliminar"].eq("apta")
        & elegibles["comparable_trekking"].eq("si")
        & elegibles["requiere_equipo_tecnico"].eq("no")
        & elegibles["decision"].isin(["pendiente", "incluir"])
        & elegibles["valores_faltantes"].eq(0)
    ).all()
    auditoria.registrar(
        "rutas",
        "elegibilidad_sin_rutas_tecnicas_ni_excluidas",
        bool(restricciones_ok),
        "Ninguna ruta elegible exige equipo técnico ni está excluida",
        "Una ruta elegible incumple calidad, actividad, equipo, decisión o completitud",
    )

    try:
        contraste_r022 = runpy.run_path(
            str(SCRIPTS / "contrastar_r022_xml_snapshot.py"), run_name="auditoria_r022"
        )["contrastar"]()
        fuente_r022_ok = contraste_r022["nodos"] == 128
        detalle_r022 = f"XML exacto, snapshot y GeoJSON concuerdan en {contraste_r022['nodos']} nodos"
    except (OSError, KeyError, ValueError, SyntaxError) as exc:
        fuente_r022_ok = False
        detalle_r022 = f"Falló el contraste de fuente R022: {exc}"
    auditoria.registrar(
        "originales",
        "R022_xml_snapshot_geojson",
        fuente_r022_ok,
        detalle_r022,
        detalle_r022,
    )

    try:
        linea_r023, datos_r023 = runpy.run_path(
            str(SCRIPTS / "procesar_r023_guagrapamba.py"), run_name="auditoria_r023"
        )["construir"]()
        fuente_r023_ok = (
            len(datos_r023["refs"]) == 26
            and datos_r023["refs"][-1] == "8146768136"
            and 0 <= datos_r023["distancia_inicio_parqueadero_m"] < 30
            and linea_r023.is_valid and linea_r023.is_simple
        )
        detalle_r023 = "XML OSM fijado por SHA-256, sendero continuo y extremo en la cascada"
    except (OSError, KeyError, ValueError, SyntaxError) as exc:
        fuente_r023_ok = False
        detalle_r023 = f"Falló la procedencia de R023: {exc}"
    auditoria.registrar("originales", "R023_xml_sendero_cascada", fuente_r023_ok, detalle_r023, detalle_r023)

    try:
        rutas_luz = runpy.run_path(
            str(SCRIPTS / "procesar_r024_r025_cerro_luz.py"), run_name="auditoria_cerro_luz"
        )["construir"]()
        fuente_luz_ok = (
            set(rutas_luz) == {"R024", "R025"}
            and all(d["refs"][-1] == "11204680653" and l.is_valid and l.is_simple for l, d in rutas_luz.values())
        )
        detalle_luz = "XML OSM fijado por SHA-256, dos senderos continuos que terminan en el mismo mirador"
    except (OSError, KeyError, ValueError, SyntaxError) as exc:
        fuente_luz_ok = False
        detalle_luz = f"Falló la procedencia de R024 y R025: {exc}"
    auditoria.registrar("originales", "R024_R025_xml_sendero_mirador", fuente_luz_ok, detalle_luz, detalle_luz)

    try:
        linea_r026, datos_r026 = runpy.run_path(
            str(SCRIPTS / "procesar_r026_guarumos.py"), run_name="auditoria_guarumos"
        )["construir"]()
        fuente_r026_ok = (
            datos_r026["refs"][0] == "352972925"
            and datos_r026["refs"][-1] == "3047618576"
            and linea_r026.is_valid and linea_r026.is_simple
        )
        detalle_r026 = "XML OSM fijado por SHA-256, sendero continuo desde la estación de desembarque hasta Cascada Guarumos"
    except (OSError, KeyError, ValueError, SyntaxError) as exc:
        fuente_r026_ok = False
        detalle_r026 = f"Falló la procedencia de R026: {exc}"
    auditoria.registrar("originales", "R026_xml_sendero_guarumos", fuente_r026_ok, detalle_r026, detalle_r026)

    try:
        _, datos_r027 = runpy.run_path(
            str(SCRIPTS / "procesar_r027_sendero_viento.py"), run_name="auditoria_sendero_viento"
        )["construir"]()
        fuente_r027_ok = (
            datos_r027["refs"][0] == "347634309"
            and datos_r027["refs"][-1] == "6797699199"
            and 0.7 < datos_r027["distancia_ida_km"] < 0.76
        )
        detalle_r027 = "XML OSM fijado por SHA-256, footway continua desde la vía de acceso hasta el sector recreativo"
    except (OSError, KeyError, ValueError, SyntaxError) as exc:
        fuente_r027_ok = False
        detalle_r027 = f"Falló la procedencia de R027: {exc}"
    auditoria.registrar("originales", "R027_xml_sendero_viento", fuente_r027_ok, detalle_r027, detalle_r027)

    for _, fila in inventario.sort_values("id_ruta").iterrows():
        id_ruta = str(fila["id_ruta"])
        originales = [valor.strip() for valor in str(fila["archivo_original"]).split("|") if valor.strip()]
        faltantes = [nombre for nombre in originales if not (ORIGINALES / "trazados" / nombre).exists()]
        auditoria.registrar(
            "originales",
            id_ruta,
            bool(originales) and not faltantes,
            f"{len(originales)} archivo(s) original(es) localizado(s)",
            f"faltan={faltantes}" if faltantes else "No se declaró archivo original",
        )

        geometria = geometria_vigente(id_ruta)
        if geometria is None:
            auditoria.registrar("geometria", id_ruta, False, "", "Debe existir exactamente un trazado GeoJSON")
        else:
            try:
                gdf = gpd.read_file(geometria)
                geom = gdf.geometry.iloc[0] if len(gdf) == 1 else None
                valida = (
                    len(gdf) == 1
                    and gdf.crs is not None
                    and gdf.crs.to_epsg() == 4326
                    and geom is not None
                    and geom.geom_type == "LineString"
                    and geom.is_valid
                    and geom.is_simple
                )
                auditoria.registrar(
                    "geometria",
                    id_ruta,
                    valida,
                    f"{geometria.name}: LineString válida, simple y EPSG:4326",
                    f"{geometria.name}: cantidad={len(gdf)}, crs={gdf.crs}, tipo={getattr(geom, 'geom_type', None)}",
                )
            except Exception as exc:  # pragma: no cover - ruta diagnóstica
                auditoria.registrar("geometria", id_ruta, False, "", f"No se pudo leer {geometria.name}: {exc}")

        raw = archivo_unico(f"03_datos_intermedios/elevacion/{id_ruta}_perfil_elevacion_raw_*.csv")
        procesado = archivo_unico(f"04_datos_procesados/perfiles/{id_ruta}_perfil_elevacion_procesado_*.csv")
        svg = archivo_unico(f"07_resultados/perfiles/{id_ruta}_perfil_elevacion_*.svg")
        auditoria.registrar(
            "perfil_raw", id_ruta, raw is not None, raw.name if raw else "", "Debe existir exactamente un perfil raw"
        )
        auditoria.registrar(
            "figura_perfil", id_ruta, svg is not None and svg.stat().st_size > 0 if svg else False,
            svg.name if svg else "", "Debe existir exactamente un SVG no vacío"
        )

        if procesado is None:
            auditoria.registrar("perfil_procesado", id_ruta, False, "", "Debe existir exactamente un perfil procesado")
            continue
        perfil = pd.read_csv(procesado)
        fila_dataset = dataset.loc[dataset["id_ruta"] == id_ruta].iloc[0]
        columnas = {
            "id_ruta", "distancia_m", "elevacion_m", "elevacion_mediana3_m", "pendiente_pct"
        }
        estructura_ok = columnas.issubset(perfil.columns)
        valores_ok = estructura_ok and (
            perfil["id_ruta"].nunique() == 1
            and str(perfil["id_ruta"].iloc[0]) == id_ruta
            and perfil["distancia_m"].is_monotonic_increasing
            and perfil["elevacion_mediana3_m"].notna().all()
            and len(perfil) == int(fila_dataset["puntos_perfil"])
        )
        tolerancia_ok = False
        if valores_ok:
            elevacion = perfil["elevacion_mediana3_m"]
            distancia_km = float(perfil["distancia_m"].iloc[-1]) / 1000
            tolerancia_ok = (
                abs(float(elevacion.min()) - float(fila_dataset["elevacion_min_m"])) <= 0.01
                and abs(float(elevacion.mean()) - float(fila_dataset["elevacion_media_m"])) <= 0.01
                and abs(float(elevacion.max()) - float(fila_dataset["elevacion_max_m"])) <= 0.01
                and abs(distancia_km - float(fila_dataset["distancia_trazado_km"])) <= 0.002
            )
        auditoria.registrar(
            "perfil_procesado",
            id_ruta,
            estructura_ok and valores_ok and tolerancia_ok,
            f"{procesado.name}: {len(perfil)} puntos, sin vacíos y métricas reconciliadas",
            f"{procesado.name}: estructura={estructura_ok}, valores={valores_ok}, reconciliacion={tolerancia_ok}",
        )

        dem = ORIGINALES / "elevacion" / str(fila_dataset["archivo_dem"])
        auditoria.registrar(
            "dem", id_ruta, dem.exists() and dem.stat().st_size > 0,
            f"{dem.name} disponible", f"No se localizó {dem.name}"
        )


def auditar_codigo_y_documentacion(auditoria: Auditoria) -> None:
    for script in sorted(SCRIPTS.glob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
            auditoria.registrar("codigo_python", script.name, True, "Sintaxis válida", "")
        except Exception as exc:
            auditoria.registrar("codigo_python", script.name, False, "", str(exc))

    for notebook in sorted(NOTEBOOKS.glob("*.ipynb")):
        try:
            contenido = json.loads(notebook.read_text(encoding="utf-8"))
            celdas = contenido.get("cells", [])
            celdas_codigo = [celda for celda in celdas if celda.get("cell_type") == "code"]
            errores_sintaxis = []
            for indice, celda in enumerate(celdas_codigo, start=1):
                try:
                    compile("".join(celda.get("source", [])), f"{notebook.name}:celda_{indice}", "exec")
                except Exception as exc:
                    errores_sintaxis.append(f"celda {indice}: {exc}")
            valido = contenido.get("nbformat") == 4 and bool(celdas) and not errores_sintaxis
            auditoria.registrar(
                "notebook", notebook.name, valido,
                f"JSON válido; {len(celdas)} celdas; {len(celdas_codigo)} celdas de código con sintaxis válida",
                "; ".join(errores_sintaxis) if errores_sintaxis else "Notebook vacío o formato distinto de nbformat 4",
            )
            celdas_sin_ejecutar = [
                indice for indice, celda in enumerate(celdas_codigo, start=1)
                if not isinstance(celda.get("execution_count"), int)
                or celda.get("execution_count") <= 0
            ]
            celdas_con_error = [
                indice for indice, celda in enumerate(celdas_codigo, start=1)
                if any(salida.get("output_type") == "error" for salida in celda.get("outputs", []))
            ]
            auditoria.registrar(
                "notebook_ejecucion", notebook.name,
                bool(celdas_codigo) and not celdas_sin_ejecutar and not celdas_con_error,
                f"{len(celdas_codigo)} celdas de código ejecutadas sin salidas de error",
                f"sin_ejecutar={celdas_sin_ejecutar}; con_error={celdas_con_error}",
            )
            if notebook.name == "04_ampliacion_rutas.ipynb":
                consolidacion = next(
                    (celda for celda in celdas_codigo if celda.get("id") == "tabla-consolidada-r001-r020"),
                    None,
                )
                texto_salidas = "" if consolidacion is None else "".join(
                    "".join(salida.get("text", []))
                    for salida in consolidacion.get("outputs", [])
                    if salida.get("output_type") == "stream"
                )
                rutas_actuales = len(pd.read_csv(RESULTADOS / "tablas" / "dataset_clasificacion_rutas.csv"))
                auditoria.registrar(
                    "notebook_vigencia", notebook.name,
                    f"Rutas inventariadas: {rutas_actuales}" in texto_salidas,
                    f"La salida de consolidación muestra las {rutas_actuales} rutas vigentes",
                    f"La salida de consolidación no muestra las {rutas_actuales} rutas vigentes",
                )
        except Exception as exc:
            auditoria.registrar("notebook", notebook.name, False, "", str(exc))

    readme = EVIDENCIAS / "README.md"
    texto = readme.read_text(encoding="utf-8")
    registrados = set(re.findall(r"(E\d{2}_[^|\s]+\.png)", texto))
    presentes = {archivo.name for archivo in EVIDENCIAS.glob("E*.png")}
    auditoria.registrar(
        "evidencias", "archivos_registrados", registrados == presentes,
        f"{len(presentes)} evidencias físicas coinciden con el registro",
        f"sin_archivo={sorted(registrados - presentes)}; sin_registro={sorted(presentes - registrados)}",
    )

    entorno = (RAIZ / "environment.yml").read_text(encoding="utf-8").lower()
    requeridas = {"python", "numpy", "pandas", "geopandas", "shapely", "rasterio", "scikit-learn", "folium", "jupyterlab"}
    faltantes = sorted(paquete for paquete in requeridas if paquete not in entorno)
    auditoria.registrar(
        "entorno", "dependencias_principales", not faltantes,
        f"{len(requeridas)} dependencias principales están declaradas",
        f"faltan={faltantes}",
    )

    docs_requeridos = [
        "criterios_seleccion_rutas.md",
        "metodologia_elevacion_piloto.md",
        "metodologia_clasificacion_recomendacion.md",
        "clasificacion_dificultad_fisica_tres_niveles_2026-10-23.md",
        "prompt_claude_interfaz_plan_final_2026-10-23.md",
        "cronograma_2026-10-07_a_2026-10-27.md",
        "registro_descargas_osm.md",
        "registro_descargas_elevacion.md",
        "diccionario_datos.csv",
    ]
    faltantes_docs = [nombre for nombre in docs_requeridos if not (DOCUMENTACION / nombre).exists()]
    auditoria.registrar(
        "documentacion", "documentos_metodologicos", not faltantes_docs,
        f"{len(docs_requeridos)} documentos esenciales localizados",
        f"faltan={faltantes_docs}",
    )

    archivo_clasificacion = RESULTADOS / "tablas" / "clasificacion_dificultad_fisica_2026-10-23.csv"
    try:
        clasificacion = pd.read_csv(archivo_clasificacion)
        conteos = clasificacion["dificultad_fisica_estimada"].value_counts().to_dict()
        ids_esperados = set(
            pd.read_csv(RESULTADOS / "tablas" / "dataset_clasificacion_rutas.csv")
            .loc[lambda df: df["estado_modelado"].eq("elegible_actual"), "id_ruta"]
        )
        ids_observados = set(clasificacion["id_ruta"])
        valido = (
            len(clasificacion) == 20
            and clasificacion["id_ruta"].is_unique
            and ids_observados == ids_esperados
            and conteos == {"Moderada": 10, "Fácil": 8, "Difícil": 2}
        )
        auditoria.registrar(
            "clasificacion_fisica", "tres_niveles", valido,
            f"20 rutas: Fácil={conteos.get('Fácil', 0)}, Moderada={conteos.get('Moderada', 0)}, Difícil={conteos.get('Difícil', 0)}",
            f"conteos={conteos}; faltan={sorted(ids_esperados - ids_observados)}; sobran={sorted(ids_observados - ids_esperados)}",
        )
    except Exception as exc:
        auditoria.registrar("clasificacion_fisica", "tres_niveles", False, "", str(exc))


def guardar_resultados(auditoria: Auditoria, dataset: pd.DataFrame) -> None:
    tabla = auditoria.tabla()
    salida_csv = RESULTADOS / "tablas" / "auditoria_integridad_proyecto.csv"
    salida_csv.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(salida_csv, index=False, encoding="utf-8")

    conteos = tabla["estado"].value_counts().to_dict()
    elegibles = int(dataset["estado_modelado"].eq("elegible_actual").sum())
    pendientes = dataset.loc[dataset["estado_modelado"].ne("elegible_actual"), "id_ruta"].tolist()
    concentracion = (
        dataset.loc[dataset["estado_modelado"].eq("elegible_actual")]
        .groupby("id_destino")
        .size()
        .sort_values(ascending=False)
    )
    rutas_dos_destinos = int(concentracion.head(2).sum())
    errores = tabla.loc[tabla["estado"].eq("ERROR"), ["ambito", "elemento", "detalle"]]
    advertencias = tabla.loc[tabla["estado"].eq("ADVERTENCIA"), ["ambito", "elemento", "detalle"]]

    lineas = [
        f"# Informe de auditoría integral del proyecto ({FECHA})",
        "",
        "## Resultado ejecutivo",
        "",
        f"- Controles ejecutados: **{len(tabla)}**.",
        f"- Controles correctos: **{conteos.get('OK', 0)}**.",
        f"- Errores estructurales: **{conteos.get('ERROR', 0)}**.",
        f"- Advertencias: **{conteos.get('ADVERTENCIA', 0)}**.",
        f"- Rutas procesadas: **{len(dataset)}**.",
        f"- Rutas elegibles para el modelo: **{elegibles}**.",
        f"- Rutas aún no elegibles: **{len(pendientes)}** ({', '.join(pendientes)}).",
        "",
        "La auditoría valida la integridad técnica del estado actual. No constituye validación externa: la clasificación principal de tres niveles tiene método y sensibilidad separados, pero no habilita recomendaciones de salida.",
        "",
        "## Alcance verificado",
        "",
        "- Concordancia de identificadores entre inventario y dataset maestro.",
        "- Unicidad del nombre por destino y exclusión de rutas técnicas del conjunto elegible.",
        "- Existencia de archivos fuente declarados y DEM utilizados; contraste del XML OSM exacto de R022, R023, R024/R025, R026 y R027, incluidos sus extremos y continuidad declarados.",
        "- Un GeoJSON por ruta, con LineString simple, válida y en EPSG:4326.",
        "- Perfiles raw y procesados, número de puntos, ausencia de vacíos y reconciliación de elevaciones y distancia.",
        "- Figura SVG por ruta.",
        "- Evidencias PNG registradas sin archivos huérfanos.",
        "- Sintaxis de scripts Python y de todas las celdas de código de los notebooks, además de su estructura JSON.",
        "- Dependencias principales y documentación metodológica.",
        "",
        "## Hallazgos que todavía requieren trabajo",
        "",
        "- R001: elegible en el conjunto actual por la variante del arenal según I10/E10; el tramo T3 y la altitud se documentan como riesgos, no como exclusión automática ni como certificación de seguridad. R007 sigue pendiente de evidencia temática.",
        "- R002: confirmar documentalmente la identidad del trazado como Los Pantzas.",
        "- R005: la línea pasa a 106.5 m de Cascada Nambillo, pero su final queda a 443.3 m; confirmar el recorrido correcto.",
        "- R009 y R010: los extremos medidos y las fuentes históricas no acreditan recorridos completos; obtener mapa o track nominal vigente y confirmar el acceso antes de incorporarlas al modelo.",
        "- R012 y R014 Yanacocha: excluidas provisionalmente del modelo hasta verificar identidad y extremos con mapa o track nominal vigente; se conservan sus originales y perfiles. R011 y R013 también requieren comprobación del recorrido completo.",
        "- R021 Yellow House: confirmar con el operador si Senderos 1 y 2 están abiertos y si la variante combinada representa una alternativa independiente; su elegibilidad es solo provisional.",
        "- R022 Cruz del Ilaló: el XML íntegro ya está archivado y concuerda con la instantánea normalizada; dos nodos de la vía figuran como `ford=yes`. Verificar los posibles vados, la apertura pública y las condiciones de acceso antes de recomendarla.",
        f"- Diversidad de la muestra: {rutas_dos_destinos} de {elegibles} rutas elegibles pertenecen a los dos lugares amplios (`id_destino`) más representados, que pueden contener llegadas distintas; evaluar su efecto en los grupos.",
        (
            f"- Con {elegibles} elegibles se alcanzó la meta mínima de 20 y la regla de dificultad física estimada ya fue evaluada por separado. Sus tres niveles pueden comunicarse con sus límites y casos sensibles; no habilitan recomendaciones automáticamente."
            if elegibles >= 20 else
            f"- Completar nuevas alternativas verificables; con {elegibles} elegibles todavía faltan {20 - elegibles} para la meta mínima de 20."
        ),
        "",
    ]
    if len(errores):
        lineas.extend(["## Errores detectados", ""])
        for fila in errores.itertuples(index=False):
            lineas.append(f"- `{fila.ambito}/{fila.elemento}`: {fila.detalle}")
        lineas.append("")
    if len(advertencias):
        lineas.extend(["## Advertencias", ""])
        for fila in advertencias.itertuples(index=False):
            lineas.append(f"- `{fila.ambito}/{fila.elemento}`: {fila.detalle}")
        lineas.append("")
    lineas.extend(
        [
            "## Reproducción",
            "",
            "Ejecutar desde la raíz del repositorio:",
            "",
            "```powershell",
            f"C:\\Users\\LENOVO\\miniforge3\\envs\\trekking_pichincha\\python.exe 06_scripts/auditar_integridad_proyecto.py --fecha {FECHA}",
            "```",
            "",
            "La tabla detallada se guarda en `07_resultados/tablas/auditoria_integridad_proyecto.csv`.",
            "",
        ]
    )
    (DOCUMENTACION / f"informe_auditoria_integridad_{FECHA}.md").write_text("\n".join(lineas), encoding="utf-8")

    print(f"Controles: {len(tabla)}")
    print(f"OK: {conteos.get('OK', 0)}")
    print(f"ADVERTENCIAS: {conteos.get('ADVERTENCIA', 0)}")
    print(f"ERRORES: {conteos.get('ERROR', 0)}")
    print(f"Rutas: {len(dataset)}; elegibles: {elegibles}")
    if conteos.get("ERROR", 0):
        sys.exit(1)


def main() -> None:
    global FECHA
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--fecha", required=True, help="Fecha real de ejecución (AAAA-MM-DD)")
    args = parser.parse_args()
    FECHA = date.fromisoformat(args.fecha).isoformat()
    inventario = pd.read_csv(DOCUMENTACION / "inventario_rutas.csv")
    dataset = pd.read_csv(RESULTADOS / "tablas" / "dataset_clasificacion_rutas.csv")
    auditoria = Auditoria()
    auditar_rutas(auditoria, inventario, dataset)
    auditar_codigo_y_documentacion(auditoria)
    guardar_resultados(auditoria, dataset)


if __name__ == "__main__":
    main()
