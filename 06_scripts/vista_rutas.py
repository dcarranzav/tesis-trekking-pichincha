"""Capa de datos de la interfaz pública (comparación neutral y visor de ruta).

Solo lee los archivos del repositorio; no modifica datos científicos ni entrena
modelos. Desde el 10/11, carga grupos K-means k=3 archivados para la página
como categorías físicas relativas y experimentales.

Usa únicamente la biblioteca estándar para que pueda probarse sin dependencias
geoespaciales.
"""

from __future__ import annotations

import csv
import datetime
import hashlib
import json
import math
import re
from pathlib import Path

from datos_mapa_dashboard import (
    RAIZ,
    TABLA,
    cargar_catalogo,
    cargar_trazado,
    gpx_desde_puntos,
    ruta_trazado,
)

INVENTARIO = RAIZ / "01_documentacion" / "inventario_rutas.csv"
PERFILES = RAIZ / "04_datos_procesados" / "perfiles"
TABLAS = RAIZ / "07_resultados" / "tablas"
VERIFICACION = RAIZ / "01_documentacion" / "verificacion_rutas_interfaz.csv"
DESTINOS = RAIZ / "01_documentacion" / "destinos_exactos_interfaz.csv"
NIVELES_FINALES = TABLAS / "niveles_esfuerzo_finales.csv"
VALIDACION_MODELO = TABLAS / "validacion_modelo_final.json"
VISOR = Path(__file__).resolve().parent / "visor_ruta"
PERFILES_CRUDOS = RAIZ / "03_datos_intermedios" / "elevacion"
CATEGORIAS_AVISOS = RAIZ / "01_documentacion" / "categorias_avisos_interfaz.csv"
ASIGNACIONES_K3 = TABLAS / "kmeans_k3_asignaciones_2026-11-10.csv"
SENSIBILIDAD_K3 = TABLAS / "kmeans_k3_sensibilidad_2026-11-10.csv"
PARAMETROS_K3 = TABLAS / "kmeans_k3_parametros_2026-11-10.json"

META_ELEGIBLES = 20
ELEGIBLE = "elegible_actual"

# Clases de pendiente local (valor absoluto, %). Son una descripción física del
# terreno estimada con DEM; NO son niveles de dificultad.
CLASES_PENDIENTE = (
    {"max": 10.0, "color": "#fde047", "etiqueta": "menos de 10 %"},
    {"max": 20.0, "color": "#fb923c", "etiqueta": "10 a 20 %"},
    {"max": 30.0, "color": "#ef4444", "etiqueta": "20 a 30 %"},
    {"max": math.inf, "color": "#9d174d", "etiqueta": "más de 30 %"},
)


# ----------------------------------------------------------------- lectura básica
def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


def cargar_inventario(ruta: Path = INVENTARIO) -> dict[str, dict[str, str]]:
    filas = _leer_csv(ruta)
    indice = {fila["id_ruta"]: fila for fila in filas}
    if len(indice) != len(filas):
        raise ValueError("El inventario contiene identificadores duplicados")
    return indice


def cargar_verificacion(ruta: Path = VERIFICACION) -> list[dict[str, str]]:
    return _leer_csv(ruta) if ruta.exists() else []


def cargar_destinos(ruta: Path = DESTINOS) -> list[dict[str, str]]:
    return _leer_csv(ruta) if ruta.exists() else []


def limpiar_alias(texto: str | None, maximo: int = 40) -> str:
    """Nombre de sesión seguro para mostrar: letras, números, espacios y - . '"""
    if not texto:
        return ""
    limpio = re.sub(r"[^\w\s\-.'áéíóúüñÁÉÍÓÚÜÑ]", "", texto, flags=re.UNICODE)
    limpio = re.sub(r"[_\s]+", " ", limpio).strip()
    return limpio[:maximo]


# ---------------------------------------------------------- lugares y destinos exactos
# Regla central: solo se comparan alternativas que llegan al MISMO destino exacto.
# El «lugar» (p. ej. un cerro) solo sirve para navegar; no agrupa rutas para comparar.
def _destino_de(fila: dict[str, str], destinos: list[dict[str, str]]) -> tuple[str, str]:
    """(lugar, destino exacto). Una ruta sin entrada en el archivo queda sola: nunca se agrupa por suposición."""
    for d in destinos:
        if d["id_ruta"] == fila["id_ruta"]:
            return d["lugar"], d["destino_exacto"]
    return fila["nombre_destino"], f"{fila['nombre_variante']} (destino exacto por definir)"


def lugares(catalogo: list[dict[str, str]], destinos: list[dict[str, str]] | None = None) -> list[dict]:
    """Lugares para navegar, con sus destinos exactos y alternativas elegibles."""
    destinos = cargar_destinos() if destinos is None else destinos
    por_lugar: dict[str, dict[str, int]] = {}
    for fila in catalogo:
        if fila["estado_modelado"] == ELEGIBLE:
            lugar, destino = _destino_de(fila, destinos)
            por_lugar.setdefault(lugar, {}).setdefault(destino, 0)
            por_lugar[lugar][destino] += 1
    return [
        {"lugar": nombre, "n_destinos": len(d), "n_alternativas": sum(d.values())}
        for nombre, d in sorted(por_lugar.items())
    ]


def destinos_de_lugar(
    catalogo: list[dict[str, str]], lugar: str, destinos: list[dict[str, str]] | None = None
) -> list[dict]:
    """Destinos exactos de un lugar con su número de alternativas elegibles."""
    destinos = cargar_destinos() if destinos is None else destinos
    conteo: dict[str, int] = {}
    for fila in catalogo:
        if fila["estado_modelado"] == ELEGIBLE:
            l, d = _destino_de(fila, destinos)
            if l == lugar:
                conteo[d] = conteo.get(d, 0) + 1
    return [{"destino": d, "n_alternativas": n} for d, n in sorted(conteo.items())]


def alternativas_de_destino(
    catalogo: list[dict[str, str]], lugar: str, destino: str, destinos: list[dict[str, str]] | None = None
) -> list[dict[str, str]]:
    """Alternativas elegibles que llegan a ese destino exacto; vacía si no existe."""
    destinos = cargar_destinos() if destinos is None else destinos
    salida = []
    for fila in catalogo:
        if fila["estado_modelado"] == ELEGIBLE and _destino_de(fila, destinos) == (lugar, destino):
            salida.append({**fila, "lugar": lugar, "destino_exacto": destino})
    return sorted(salida, key=lambda r: r["id_ruta"])


def validar_comparacion(alternativas: list[dict[str, str]]) -> None:
    """Impide comparar alternativas con destinos finales distintos."""
    if len({(a["lugar"], a["destino_exacto"]) for a in alternativas}) > 1:
        raise ValueError("No se pueden comparar alternativas que llegan a destinos finales distintos.")


def hay_comparacion(alternativas: list) -> bool:
    return len(alternativas) >= 2


# ------------------------------------------------------------- estados de las rutas
def conteo_estados(catalogo: list[dict[str, str]], habilitadas: list[str] | None = None) -> dict:
    """Tres estados distintos: procesada, elegible provisional para el estudio y habilitada para recomendar.

    «Habilitada para recomendación» exige verificación de acceso y modelo final: hoy es 0.
    """
    elegibles = sum(1 for fila in catalogo if fila["estado_modelado"] == ELEGIBLE)
    return {
        "procesadas": len(catalogo),
        "elegibles_provisionales": elegibles,
        "no_elegibles": len(catalogo) - elegibles,
        "habilitadas_recomendacion": len(habilitadas or []),
    }


# ------------------------------------------------------------- estado de la clasificación
def validacion_modelo(
    ruta_niveles: Path, ruta_validacion: Path, elegibles: int, ids_elegibles: set[str] | None = None
) -> tuple[bool, str]:
    """Comprueba la validación EXPLÍCITA del modelo final. Alcanzar 20 rutas y crear un CSV no basta.

    El registro de validación (JSON) debe declarar: aprobado=true, quién aprobó, fecha, versión del modelo,
    número de rutas elegibles y el SHA-256 exacto del archivo de niveles. Cualquier cambio posterior del
    archivo o de la muestra invalida la aprobación.
    """
    if not ruta_niveles.exists():
        return False, "no existe el archivo de niveles finales"
    if not ruta_validacion.exists():
        return False, "falta el registro de validación explícita del modelo final"
    try:
        registro = json.loads(ruta_validacion.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, "el registro de validación no se puede leer"
    if not isinstance(registro, dict) or registro.get("aprobado") is not True:
        return False, "el modelo final no está aprobado"
    for campo in ("aprobado_por", "fecha", "version_modelo"):
        if not str(registro.get(campo, "")).strip():
            return False, f"el registro de validación no indica {campo}"
    try:
        fecha = datetime.date.fromisoformat(str(registro["fecha"]))
    except ValueError:
        return False, "la fecha de validación no es válida"
    if fecha > datetime.date.today():
        return False, "la fecha de validación es futura"
    if registro.get("n_rutas_elegibles") != elegibles:
        return False, "la validación corresponde a otra muestra de rutas"
    huella = hashlib.sha256(ruta_niveles.read_bytes()).hexdigest()
    if registro.get("sha256_niveles") != huella:
        return False, "el archivo de niveles cambió después de la validación"
    if ids_elegibles is not None:
        ids_archivo = {f["id_ruta"] for f in _leer_csv(ruta_niveles) if "id_ruta" in f}
        if ids_archivo != ids_elegibles:
            return False, "los niveles no cubren exactamente las rutas elegibles"
    return True, "validado"


def estado_clasificacion(
    catalogo: list[dict[str, str]],
    ruta_niveles: Path = NIVELES_FINALES,
    meta: int = META_ELEGIBLES,
    ruta_validacion: Path = VALIDACION_MODELO,
) -> dict:
    """Estado de publicación de niveles finales; el K-means descriptivo se consulta aparte."""
    ids = {fila["id_ruta"] for fila in catalogo if fila["estado_modelado"] == ELEGIBLE}
    elegibles = len(ids)
    faltan = max(0, meta - elegibles)
    validada, motivo = validacion_modelo(ruta_niveles, ruta_validacion, elegibles, ids)
    disponible = validada and faltan == 0
    if disponible:
        mensaje = "Clasificación de exigencia física disponible (modelo final validado explícitamente)."
    elif faltan:
        mensaje = (
            f"Publicación de niveles finales en desarrollo: hay {elegibles} alternativas elegibles de las {meta} "
            "que exige la metodología. Los resultados exploratorios se informan por separado."
        )
    else:
        mensaje = (
            f"El K-means descriptivo asigna clases físicas relativas a la muestra de {elegibles} rutas. "
            f"La publicación de niveles finales sigue en desarrollo y no se habilita la elección de salidas: {motivo}."
        )
    return {
        "disponible": disponible, "elegibles": elegibles, "meta": meta, "faltan": faltan,
        "mensaje": mensaje, "motivo_bloqueo": "" if disponible else (motivo if not faltan else f"faltan {faltan} rutas"),
    }


# --------------------------------------------------------------------- perfiles
def ruta_perfil(id_ruta: str, carpeta: Path = PERFILES) -> Path:
    if not re.fullmatch(r"R\d{3}", id_ruta):
        raise ValueError("Identificador de ruta inválido")
    archivos = sorted(carpeta.glob(f"{id_ruta}_perfil_elevacion_procesado_*.csv"))
    if not archivos:
        raise FileNotFoundError(f"No existe perfil procesado para {id_ruta}")
    return max(archivos, key=lambda p: p.stem.rsplit("_", 1)[-1])


def cargar_perfil(id_ruta: str, carpeta: Path = PERFILES) -> list[dict[str, float | None]]:
    ruta = ruta_perfil(id_ruta, carpeta)
    puntos = []
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            if fila["id_ruta"] != id_ruta:
                raise ValueError(f"{id_ruta}: el perfil contiene otra ruta")
            pend = fila.get("pendiente_pct", "")
            punto = {
                "d": float(fila["distancia_m"]),
                "lat": float(fila["latitud"]),
                "lon": float(fila["longitud"]),
                "elev": float(fila["elevacion_mediana3_m"]),
                "pend": float(pend) if pend not in ("", None) else None,
            }
            if not all(math.isfinite(v) for v in punto.values() if v is not None):
                raise ValueError(f"{id_ruta}: valor no finito en el perfil")
            puntos.append(punto)
    if len(puntos) < 2:
        raise ValueError(f"{id_ruta}: el perfil necesita al menos dos puntos")
    if any(b["d"] <= a["d"] for a, b in zip(puntos, puntos[1:])):
        raise ValueError(f"{id_ruta}: las distancias del perfil no son crecientes")
    return puntos


def fuente_elevacion(id_ruta: str, carpeta: Path = PERFILES) -> tuple[str, str]:
    """(fuente DEM, método de filtrado) tal como constan en el perfil procesado."""
    with ruta_perfil(id_ruta, carpeta).open(encoding="utf-8", newline="") as archivo:
        primera = next(csv.DictReader(archivo))
    return primera["fuente_elevacion"], primera["metodo_filtrado"]


def trayecto_simulado(perfil: list[dict], tipo_recorrido: str) -> dict:
    """Recorrido para la simulación. Ida y vuelta: regreso por la misma traza (no es un registro GPS)."""
    ida = perfil
    largo = ida[-1]["d"]
    puntos = [dict(p, pend=(p["pend"] or 0.0)) for p in ida]
    giro = None
    if tipo_recorrido != "circular":
        giro = len(puntos) - 1
        for i in range(len(ida) - 2, -1, -1):
            pend_ida = ida[i + 1]["pend"] or 0.0
            puntos.append(
                {
                    "d": largo + (largo - ida[i]["d"]),
                    "lat": ida[i]["lat"],
                    "lon": ida[i]["lon"],
                    "elev": ida[i]["elev"],
                    "pend": -pend_ida,
                }
            )
    return {
        "puntos": puntos,
        "giro": giro,
        "ida_m": largo,
        "total_m": puntos[-1]["d"],
        "circular": tipo_recorrido == "circular",
    }


def clase_pendiente(pend_abs: float) -> int:
    for indice, clase in enumerate(CLASES_PENDIENTE):
        if pend_abs < clase["max"]:
            return indice
    return len(CLASES_PENDIENTE) - 1


# ------------------------------------------------------------------ avisos y acceso
def verificar_acceso(
    fila: dict[str, str], inicio: tuple[float, float], verificacion: list[dict[str, str]] | None = None
) -> dict:
    """Nombre de acceso que puede mostrarse. Si no está contrastado, se avisa y se dan las coordenadas."""
    verificacion = cargar_verificacion() if verificacion is None else verificacion
    for registro in verificacion:
        if registro["clave"] == fila["id_ruta"] and registro["tipo"] == "nombre_acceso":
            if registro["estado"] != "verificado":
                return {
                    "estado": registro["estado"],
                    "etiqueta": f"Acceso por verificar · inicio en {inicio[0]:.4f}, {inicio[1]:.4f}",
                    "nota": registro["texto"],
                }
    return {"estado": "segun_fuente", "etiqueta": fila["nombre_variante"], "nota": ""}


def _solapamientos(id_ruta: str, carpeta: Path = TABLAS) -> list[str]:
    archivos = sorted(carpeta.glob("solapamiento_rutas_*.csv"))
    if not archivos:
        return []
    avisos = []
    for fila in _leer_csv(max(archivos, key=lambda p: p.stem.rsplit("_", 1)[-1])):
        if fila["tramo_compartido_relevante"] != "True":
            continue
        if fila["id_ruta_a"] == id_ruta:
            otra, propia, ajena = fila["id_ruta_b"], fila["fraccion_a_cubierta_20m"], fila["fraccion_b_cubierta_20m"]
        elif fila["id_ruta_b"] == id_ruta:
            otra, propia, ajena = fila["id_ruta_a"], fila["fraccion_b_cubierta_20m"], fila["fraccion_a_cubierta_20m"]
        else:
            continue
        avisos.append(
            f"Comparte parte del trazado con {otra}: {float(propia) * 100:.0f} % de esta ruta queda a menos de "
            f"20 m de esa alternativa ({float(ajena) * 100:.0f} % en sentido contrario)."
        )
    return avisos


def advertencias_destacadas(id_ruta: str, verificacion: list[dict[str, str]] | None = None) -> list[str]:
    """Avisos que la página muestra de forma visible junto a la ruta (p. ej. alta montaña y tramo T3)."""
    verificacion = cargar_verificacion() if verificacion is None else verificacion
    return [r["texto"] for r in verificacion if r["clave"] == id_ruta and r["tipo"] == "destacada"]


def advertencias(id_ruta: str, verificacion: list[dict[str, str]] | None = None) -> list[str]:
    verificacion = cargar_verificacion() if verificacion is None else verificacion
    textos = [
        "Elegibilidad provisional para el análisis estadístico: no confirma que el sendero esté abierto ni transitable."
    ]
    textos += advertencias_destacadas(id_ruta, verificacion)
    textos += [r["texto"] for r in verificacion if r["clave"] == id_ruta and r["tipo"] == "advertencia"]
    textos += _solapamientos(id_ruta)
    return textos


def notas_de_lugar(lugar: str, verificacion: list[dict[str, str]] | None = None) -> list[str]:
    verificacion = cargar_verificacion() if verificacion is None else verificacion
    return [r["texto"] for r in verificacion if r["tipo"] == "en_investigacion" and r["clave"] == lugar]



# ------------------------------------------------- índice de esfuerzo de referencia (descriptivo)
# Decisión metodológica compartida (2026-10-22): HEN = distancia/5 + ascenso/600 (regla de Naismith).
# Es una referencia ESTIMADA para comparar alternativas del MISMO destino exacto. No es una duración
# prevista, no es una clase de dificultad, no es una recomendación ni un intervalo de confianza.
V_REFERENCIA_KMH = 5.0
R_REFERENCIA_M_H = 600.0
ROTULO_INDICE = "Índice de esfuerzo de referencia (h-eq)"
UNIDAD_INDICE = "h-eq"
AVISO_INDICE = (
    "Es una referencia estimada con la regla de Naismith (distancia ÷ 5 km/h + ascenso ÷ 600 m/h). "
    "No es la duración prevista de la caminata ni mide la dificultad, y solo sirve para comparar "
    "alternativas del mismo destino exacto."
)
AVISO_ORDEN = (
    "Orden por índice de esfuerzo de referencia, de menor a mayor. No indica cuál alternativa elegir: "
    "no se evalúan acceso, estado del sendero, altitud ni aptitud personal."
)
AVISO_SENSIBILIDAD = (
    "Esta comparación **no es un intervalo de confianza**: solo muestra cuánto cambia el índice según cómo se "
    "trate el ruido del modelo de elevación. El valor «crudo» conserva el ruido del DEM y puede sobrestimar el "
    "ascenso; el valor «filtrado» (mediana de 3 puntos) puede subestimar relieve real menor que una celda de 30 m. "
    "El valor verdadero no tiene por qué estar entre ambos."
)


def horas_equivalentes(distancia_km: float, ascenso_m: float) -> float:
    """HEN = distancia_km / 5 + ascenso_m / 600. Solo depende de distancia y ascenso (no de la altitud)."""
    return float(distancia_km) / V_REFERENCIA_KMH + float(ascenso_m) / R_REFERENCIA_M_H


def indice_esfuerzo(fila: dict[str, str]) -> dict[str, float]:
    """Índice de la alternativa con los datos validados del dataset (ascenso con mediana de 3 puntos)."""
    distancia, ascenso = float(fila["distancia_total_km"]), float(fila["ascenso_total_m"])
    return {
        "valor": horas_equivalentes(distancia, ascenso),
        "parte_distancia": distancia / V_REFERENCIA_KMH,
        "parte_ascenso": ascenso / R_REFERENCIA_M_H,
    }


def formato_indice(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


def ordenar_por_indice(alternativas: list[dict[str, str]]) -> list[dict[str, str]]:
    """Ordena de menor a mayor índice SOLO si todas llegan al mismo destino exacto (si no, falla)."""
    if alternativas:
        validar_comparacion(alternativas)
    return sorted(alternativas, key=lambda f: (round(indice_esfuerzo(f)["valor"], 6), f["id_ruta"]))


def coincidencias_limites(
    alternativas: list[dict[str, str]], distancia_max_km: float | None = None,
    ascenso_max_m: float | None = None,
) -> list[dict]:
    """Marca coincidencia con límites declarados, sin recomendar ni certificar seguridad.

    Se evalúan todas las alternativas del mismo destino exacto. La salida
    conserva las que exceden un límite para que el visitante vea por qué no
    coinciden, en lugar de ocultarlas o presentarlas como rutas prohibidas.
    """
    validar_comparacion(alternativas)
    limites = {}
    for nombre, limite in (("distancia_max_km", distancia_max_km), ("ascenso_max_m", ascenso_max_m)):
        try:
            numero = None if limite is None else float(limite)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{nombre} debe ser numérico") from error
        if numero is not None and (not math.isfinite(numero) or numero <= 0):
            raise ValueError(f"{nombre} debe ser positivo y finito")
        limites[nombre] = numero
    salida = []
    for fila in ordenar_por_indice(alternativas):
        distancia = float(fila["distancia_total_km"])
        ascenso = float(fila["ascenso_total_m"])
        if not math.isfinite(distancia) or not math.isfinite(ascenso) or distancia <= 0 or ascenso < 0:
            raise ValueError(f"Métricas inválidas en {fila['id_ruta']}")
        razones = []
        if limites["distancia_max_km"] is not None and distancia > limites["distancia_max_km"]:
            razones.append("supera la distancia indicada")
        if limites["ascenso_max_m"] is not None and ascenso > limites["ascenso_max_m"]:
            razones.append("supera el ascenso indicado")
        salida.append({"id_ruta": fila["id_ruta"], "coincide": not razones,
                       "razones": razones, "indice_referencia": indice_esfuerzo(fila)["valor"]})
    return salida


def grupo_kmeans_descriptivo(
    id_ruta: str,
    catalogo: list[dict[str, str]] | None = None,
    archivo: Path = RAIZ / "07_resultados" / "tablas" / "modelo_kmeans_fisico_asignaciones_2026-10-22.csv",
) -> dict:
    """Lee el K-means físico relativo solo si cubre la muestra elegible actual.

    No sirve para certificar aptitud, acceso o seguridad de una ruta.
    """
    catalogo = cargar_catalogo() if catalogo is None else catalogo
    elegibles = {fila["id_ruta"] for fila in catalogo if fila["estado_modelado"] == ELEGIBLE}
    with archivo.open(encoding="utf-8-sig", newline="") as fuente:
        filas = list(csv.DictReader(fuente))
    asignaciones = {f["id_ruta"]: int(f["grupo_relativo_k2"]) for f in filas}
    if len(asignaciones) != len(filas) or set(asignaciones) != elegibles or set(asignaciones.values()) != {0, 1}:
        raise ValueError("Las asignaciones K-means no corresponden a la muestra elegible actual")
    if id_ruta not in asignaciones:
        raise ValueError("La ruta no pertenece al análisis K-means actual")
    grupo = asignaciones[id_ruta]
    seleccion = next(f for f in filas if f["id_ruta"] == id_ruta)
    return {
        "grupo": grupo,
        "descripcion": "Mayor exigencia física estimada (relativa)" if grupo == 1 else "Menor exigencia física estimada (relativa)",
        "tamano": sum(valor == grupo for valor in asignaciones.values()),
        "total": len(asignaciones),
        "sensible": seleccion["sensible_a_parametros"] == "si",
    }


def archivo_clasificacion_dificultad(carpeta: Path = TABLAS) -> Path:
    """Archivo de la regla de marcha anterior, conservado para contraste."""
    archivos = sorted(carpeta.glob("clasificacion_dificultad_fisica_????-??-??.csv"))
    if not archivos:
        raise FileNotFoundError("No existe la clasificación Fácil/Moderada/Difícil")
    return archivos[-1]


def dificultad_fisica_estimada(
    id_ruta: str,
    catalogo: list[dict[str, str]] | None = None,
    archivo: Path | None = None,
) -> dict:
    """Lee el nivel de la regla de marcha histórica si cubre la muestra actual.

    Esta categoría no habilita recomendaciones y no representa técnica, acceso,
    estado del sendero, clima, seguridad ni aptitud personal.
    """
    catalogo = cargar_catalogo() if catalogo is None else catalogo
    elegibles = {fila["id_ruta"] for fila in catalogo if fila["estado_modelado"] == ELEGIBLE}
    archivo = archivo or archivo_clasificacion_dificultad()
    filas = _leer_csv(archivo)
    por_id = {fila["id_ruta"]: fila for fila in filas}
    if len(por_id) != len(filas) or set(por_id) != elegibles:
        raise ValueError("La clasificación de tres niveles no corresponde a la muestra elegible actual")
    if {fila["dificultad_fisica_estimada"] for fila in filas} != {"Fácil", "Moderada", "Difícil"}:
        raise ValueError("La clasificación no contiene exactamente los tres niveles previstos")
    if id_ruta not in por_id:
        raise ValueError("La ruta no pertenece a la clasificación física actual")
    fila = por_id[id_ruta]
    return {
        "nivel": fila["dificultad_fisica_estimada"],
        "orden": int(fila["nivel_orden"]),
        "horas_estimadas": float(fila["horas_marcha_efectiva_estimadas"]),
        "sensible": fila["sensible_a_supuestos"] == "si",
        "escenarios_cambio": [x for x in fila["escenarios_cambio"].split("|") if x],
        "metodo": fila["metodo"],
        "advertencia": fila["advertencia"],
    }


def clasificacion_kmeans_k3(catalogo: list[dict[str, str]] | None = None,
                             archivo: Path = ASIGNACIONES_K3,
                             sensibilidad: Path = SENSIBILIDAD_K3,
                             parametros: Path = PARAMETROS_K3) -> dict[str, dict]:
    """Grupos k=3 archivados para la página; relativos a las 20 rutas del estudio.

    La regla de horas se conserva como contraste, pero no asigna estas etiquetas.
    Se rechaza una muestra distinta o valores distintos de los que se agruparon.
    """
    catalogo = cargar_catalogo() if catalogo is None else catalogo
    elegibles = {f["id_ruta"]: f for f in catalogo if f["estado_modelado"] == ELEGIBLE}
    filas = _leer_csv(archivo)
    por_id = {f["id_ruta"]: f for f in filas}
    if len(filas) != len(por_id) or set(por_id) != set(elegibles):
        raise ValueError("Las asignaciones K-means no corresponden a las rutas elegibles actuales")
    modelo = json.loads(parametros.read_text(encoding="utf-8"))
    if set(modelo["ids_entrenamiento"]) != set(elegibles) or modelo["variables"] != ["distancia_total_km", "ascenso_total_m"]:
        raise ValueError("Los parámetros K-means no corresponden a la muestra y variables actuales")
    medias, desvios = modelo["media_entrenamiento"], modelo["desviacion_entrenamiento"]
    centros = modelo["centroides_estandarizados_k3"]
    if len(medias) != 2 or len(desvios) != 2 or len(centros) != 3 or any(len(c) != 2 for c in centros):
        raise ValueError("Parámetros K-means incompletos")
    nombres = ("Fácil", "Moderada", "Difícil")
    cambios: dict[str, list[str]] = {}
    for escenario in _leer_csv(sensibilidad):
        if escenario["n_rutas"] != str(len(elegibles)) or escenario["escenario"] == "mas_elevacion_maxima":
            continue  # la altitud es exposición; no es una variable de esfuerzo del modelo
        for id_ruta in filter(None, escenario["rutas_cambian_de_grupo"].split("|")):
            cambios.setdefault(id_ruta, []).append(escenario["escenario"])
    resultado = {}
    for id_ruta, fila in por_id.items():
        grupo = int(fila["grupo_k3"])
        if grupo not in (0, 1, 2):
            raise ValueError(f"Grupo K-means inválido en {id_ruta}")
        actual = elegibles[id_ruta]
        for campo in ("distancia_total_km", "ascenso_total_m"):
            if abs(float(fila[campo]) - float(actual[campo])) > 0.001:
                raise ValueError(f"{id_ruta}: el valor de {campo} difiere del utilizado por K-means")
        z = [(float(fila[campo]) - medias[i]) / desvios[i]
             for i, campo in enumerate(("distancia_total_km", "ascenso_total_m"))]
        grupo_calculado = min(range(3), key=lambda i: sum((z[j] - centros[i][j]) ** 2 for j in range(2)))
        if grupo_calculado != grupo:
            raise ValueError(f"{id_ruta}: la asignación difiere del centroide K-means archivado")
        resultado[id_ruta] = {
            "nivel": nombres[grupo], "orden": grupo + 1, "grupo": grupo,
            "sensible": bool(cambios.get(id_ruta)), "escenarios_cambio": cambios.get(id_ruta, []),
            "cerca_de_frontera": fila["cerca_de_frontera"] == "si",
            "metodo": "K-means k=3 sobre distancia total y ascenso acumulado estandarizados",
        }
    if set(r["nivel"] for r in resultado.values()) != set(nombres):
        raise ValueError("K-means no produjo los tres niveles esperados")
    return resultado


def ruta_perfil_crudo(id_ruta: str, carpeta: Path = PERFILES_CRUDOS) -> Path:
    if not re.fullmatch(r"R\d{3}", id_ruta):
        raise ValueError("Identificador de ruta inválido")
    archivos = sorted(carpeta.glob(f"{id_ruta}_perfil_elevacion_raw_*.csv"))
    if not archivos:
        raise FileNotFoundError(f"No existe perfil de elevación sin filtrar para {id_ruta}")
    return max(archivos, key=lambda p: p.stem.rsplit("_", 1)[-1])


def ascenso_crudo_total(id_ruta: str, tipo_recorrido: str, carpeta: Path = PERFILES_CRUDOS) -> float:
    """Ascenso total del perfil sin filtrar, con la misma convención del dataset (ida y vuelta = subida + bajada)."""
    elevaciones = []
    with ruta_perfil_crudo(id_ruta, carpeta).open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            if fila["id_ruta"] != id_ruta:
                raise ValueError(f"{id_ruta}: el perfil sin filtrar contiene otra ruta")
            elevaciones.append(float(fila["elevacion_m"]))
    if len(elevaciones) < 2 or not all(math.isfinite(e) for e in elevaciones):
        raise ValueError(f"{id_ruta}: perfil sin filtrar inválido")
    cambios = [b - a for a, b in zip(elevaciones, elevaciones[1:])]
    subida = sum(c for c in cambios if c > 0)
    bajada = -sum(c for c in cambios if c < 0)
    return subida + bajada if tipo_recorrido != "circular" else subida


def sensibilidad_dem(fila: dict[str, str], carpeta: Path = PERFILES_CRUDOS) -> dict[str, float]:
    """Índice con el ascenso filtrado (base) y con el ascenso sin filtrar. Descriptivo: no es un intervalo."""
    distancia = float(fila["distancia_total_km"])
    filtrado = float(fila["ascenso_total_m"])
    crudo = ascenso_crudo_total(fila["id_ruta"], fila["tipo_recorrido"], carpeta)
    return {
        "ascenso_filtrado_m": filtrado,
        "ascenso_crudo_m": crudo,
        "indice_filtrado": horas_equivalentes(distancia, filtrado),
        "indice_crudo": horas_equivalentes(distancia, crudo),
    }


# ------------------------------------------------ avisos separados: altitud, acceso, carácter técnico
CATEGORIAS = ("altitud", "acceso", "caracter_tecnico")


def cargar_categorias(ruta: Path = CATEGORIAS_AVISOS) -> list[dict[str, str]]:
    return _leer_csv(ruta) if ruta.exists() else []


def avisos_separados(
    id_ruta: str,
    fila: dict[str, str],
    inventario: dict[str, dict[str, str]],
    verificacion: list[dict[str, str]] | None = None,
    categorias: list[dict[str, str]] | None = None,
    nota_acceso: str = "",
) -> dict[str, list[str]]:
    """Avisos agrupados en altitud, acceso, carácter técnico y otros. Ningún aviso se descarta.

    Cada fila de `verificacion` se asigna a las categorías que indica `categorias_avisos_interfaz.csv`;
    las que no figuren allí quedan en «otros». La altitud se informa siempre como valor y nunca entra en el índice.
    """
    verificacion = cargar_verificacion() if verificacion is None else verificacion
    categorias = cargar_categorias() if categorias is None else categorias
    asignadas = {(c["clave"], c["tipo"]): set() for c in categorias}
    for c in categorias:
        if c["categoria"] not in CATEGORIAS:
            raise ValueError(f"Categoría de aviso desconocida: {c['categoria']}")
        asignadas[(c["clave"], c["tipo"])].add(c["categoria"])
    salida: dict[str, list[str]] = {"altitud": [], "acceso": [], "caracter_tecnico": [], "otros": []}
    salida["altitud"].append(
        f"Altitud máxima del trazado: {float(fila['elevacion_max_m']):,.0f} m (estimada con un DEM de 30 m)."
        .replace(",", " ") + " No forma parte del índice de esfuerzo."
    )
    equipo = inventario.get(id_ruta, {}).get("requiere_equipo_tecnico", "").strip()
    etiqueta_equipo = {"no": "no", "por_verificar": "por confirmar"}.get(equipo, equipo or "sin dato")
    salida["caracter_tecnico"].append(
        f"Inventario: requiere equipo técnico → {etiqueta_equipo}. El criterio y su fuente están en «Fuentes, licencias y estado»."
    )
    salida["acceso"].append(
        "Elegibilidad provisional para el análisis estadístico: no confirma que el sendero esté abierto ni transitable."
    )
    if nota_acceso:
        salida["acceso"].append(nota_acceso)
    for registro in verificacion:
        if registro["clave"] != id_ruta or registro["tipo"] not in ("destacada", "advertencia"):
            continue
        destinos = asignadas.get((registro["clave"], registro["tipo"]), set())
        for categoria in (destinos or {"otros"}):
            salida[categoria].append(registro["texto"])
    salida["otros"] += _solapamientos(id_ruta)
    return salida


# ------------------------------------------------------------------- visor y GPX
def datos_visor(id_ruta: str, fila: dict[str, str]) -> dict:
    """Todo lo que necesita el visor, calculado desde el GeoJSON y el perfil procesado."""
    _, linea = cargar_trazado(id_ruta)
    perfil = cargar_perfil(id_ruta)
    trayecto = trayecto_simulado(perfil, fila["tipo_recorrido"])
    puntos = trayecto["puntos"]
    return {
        "id": id_ruta,
        "titulo": fila["nombre_ruta"],
        "circular": trayecto["circular"],
        "giro": trayecto["giro"],
        "ida_m": round(trayecto["ida_m"], 1),
        "total_m": round(trayecto["total_m"], 1),
        "d": [round(p["d"], 1) for p in puntos],
        "lat": [round(p["lat"], 6) for p in puntos],
        "lon": [round(p["lon"], 6) for p in puntos],
        "elev": [round(p["elev"], 1) for p in puntos],
        "pend": [round(p["pend"], 1) for p in puntos],
        "linea": [[round(lat, 6), round(lon, 6)] for lat, lon in linea],
        "clases": [
            {"max": (None if math.isinf(c["max"]) else c["max"]), "color": c["color"], "etiqueta": c["etiqueta"]}
            for c in CLASES_PENDIENTE
        ],
    }


def construir_visor_html(datos: dict) -> str:
    """Página autónoma: Leaflet incluido en el archivo; solo las teselas requieren internet."""
    plantilla = (VISOR / "plantilla.html").read_text(encoding="utf-8")
    js = (VISOR / "leaflet.js").read_text(encoding="utf-8")
    css = (VISOR / "leaflet.css").read_text(encoding="utf-8")
    if "</script" in js.lower():
        raise ValueError("leaflet.js contiene una etiqueta de cierre de script")
    carga = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    for caracter, escape in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        carga = carga.replace(caracter, escape)
    return plantilla.replace("__LEAFLET_CSS__", css).replace("__LEAFLET_JS__", js).replace("__DATOS__", carga)


def gpx_ida(id_ruta: str, nombre: str) -> bytes:
    """GPX 2D de la ida, derivado del GeoJSON documentado: sin elevaciones ni tiempos."""
    _, puntos = cargar_trazado(id_ruta)
    return gpx_desde_puntos(id_ruta, nombre, puntos)

