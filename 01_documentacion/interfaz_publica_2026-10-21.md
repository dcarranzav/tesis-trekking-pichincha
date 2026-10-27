# Interfaz de comparación y visualización de rutas — 21 de octubre de 2026

**Estado metodológico vigente (23 de octubre):** la capa de datos contiene Fácil/Moderada/Difícil para las 20 rutas; la pantalla todavía refleja el diseño anterior de dos clases y está pendiente de la adaptación indicada al final de este documento. No hay recomendaciones de salida ni afirmaciones de seguridad.

## Qué hace

1. **Ingreso con nombre, sin base de datos.** Para explorar se pide un nombre al inicio. Vive solo en la memoria de la visita y se limpia de caracteres especiales antes de mostrarse.
2. **Elegir un lugar y luego un destino exacto.** El lugar (un cerro, una reserva) solo sirve para navegar. Cada lugar se separa en destinos exactos (p. ej. «Cima del Cerro Ilaló» y «Cruz del Ilaló»; en Mindo: Cascada Corazón, Mirador y Yellow House). Aparecen las 20 rutas con `estado_modelado=elegible_actual`, que son **elegibles provisionales para el estudio**: no están «verificadas» ni habilitadas para recomendar.
3. **Comparar alternativas del mismo destino exacto.** Nunca se comparan destinos finales distintos (`vista_rutas.validar_comparacion`). Tarjetas y tabla ordenable con inicio, llegada, tipo, distancia total, ascenso, elevación máxima, pendiente media y p95, y fuente del trazado. El índice continuo de esfuerzo de referencia (h-eq) ordena las alternativas de menor a mayor solo dentro del mismo destino: no indica duración prevista ni cuál elegir. Un destino con una sola alternativa lo indica y no muestra tabla; no se obliga a tener tres.
4. **Ver el recorrido.** Mapa OpenStreetMap/OpenTopoMap con el trazado coloreado por pendiente local, inicio, llegada, marcas por kilómetro, perfil de elevación sincronizado con la posición y **simulación** de ida y regreso (reproducir, pausar, reiniciar, ritmo y control deslizante accesible por teclado). Con «reducir movimiento» activado en el sistema, la animación se desactiva y queda el control deslizante.
5. **Avisos, fuentes y descargas.** La altitud, el acceso y el carácter técnico se muestran por separado. El índice incluye un detalle desplegable sobre el ascenso filtrado y crudo; esa sensibilidad del DEM no es un intervalo de confianza. Hay panel de fuente/licencia/estado de validación, «¿Cómo se calculó?», GeoJSON y GPX de la ida (sin elevaciones ni tiempos).

## Reglas que respeta

- Los colores del mapa describen **pendiente local** (menos de 10 %, 10–20 %, 20–30 %, más de 30 %); no son dificultad.
- `estado_clasificacion()` conserva bloqueada la habilitación de niveles finales y recomendaciones mientras no existan `niveles_esfuerzo_finales.csv` y su validación explícita. Las clases físicas relativas K-means que muestra la página son un resultado descriptivo separado y no levantan ese bloqueo.
- La animación es una simulación a ritmo constante: no representa tiempo real ni un registro GPS. El regreso usa la misma traza de la ida.
- No se modificó ningún dato científico (inventario, dataset, GeoJSON, perfiles, DEM).

## Ilaló y el nombre del acceso de R006

- El inventario llama a R006 «El Tingo - cima», pero su GeoJSON empieza en -0,2440; -78,4274, unos 4,5 km **al norte** del inicio de R022 (Los Olivos, -0,2836; -78,4369). Ese nombre no se ha contrastado con OpenStreetMap ni con un mapa oficial, así que la interfaz muestra «Acceso por verificar» con las coordenadas reales y no lo presenta como El Tingo. No se renombró la ruta ni se movió la línea (`verificacion_rutas_interfaz.csv`).
- R006 (cima) y R022 (Cruz del Ilaló) llegan a puntos distintos (≈1,3 km). Son destinos exactos separados bajo el lugar «Cerro Ilaló»: nunca aparecen en la misma tabla ni se cuentan como alternativas equivalentes (`destinos_exactos_interfaz.csv`). Esta regla se aplica a todo el inventario.

## Estados de una ruta

- **Procesada** (27): tiene trazado y medidas calculadas.
- **Elegible provisional para el estudio** (20): cumple los criterios estadísticos actuales; no confirma apertura, acceso ni seguridad.
- **Habilitada para recomendación** (0): exige verificar acceso y contar con el modelo final; ninguna lo está.
- La Merced y Cumbayá/Tumbaco no tienen trazado continuo y verificable en el inventario; aparecen como «en investigación» y no se dibujan.

## Archivos nuevos o modificados

| Archivo | Función |
|---|---|
| `app.py` | Página Streamlit (reemplaza el prototipo anterior; el anterior está en el historial de Git) |
| `06_scripts/vista_rutas.py` | Datos de la interfaz: agrupación, perfiles, trayecto simulado, avisos, visor y GPX (solo biblioteca estándar) |
| `06_scripts/visor_ruta/plantilla.html` | Visor autónomo: mapa, perfil, simulación |
| `06_scripts/visor_ruta/leaflet.js`, `leaflet.css`, `LICENSE-leaflet.txt` | Leaflet 1.9.4 (BSD-2) incluido con su suma SHA-256; no depende de un CDN |
| `01_documentacion/verificacion_rutas_interfaz.csv` | Avisos y estado del nombre de acceso, cada uno con su documento de origen |
| `01_documentacion/destinos_exactos_interfaz.csv` | Lugar → destino exacto de cada ruta, con el criterio (llegadas coincidentes o distintas) |
| `tests/test_vista_rutas.py`, `tests/test_app_humo.py` | Pruebas nuevas |
| `requirements.txt` | Dependencias mínimas para la nube |

## Ejecutar localmente

```powershell
$py = 'C:\Users\LENOVO\miniforge3\envs\trekking_pichincha\python.exe'
& $py -m streamlit run app.py
```

Abrir `http://localhost:8501`. Las teselas necesitan internet; sin conexión se muestra solo el trazado con un aviso.

## Ejecutar en la nube (Streamlit Community Cloud)

1. Subir el repositorio a GitHub (solo con autorización expresa; ver reglas del proyecto).
2. En share.streamlit.io elegir el repositorio, la rama y `app.py` como archivo principal.
3. La plataforma instala `requirements.txt` (solo Streamlit). La app lee los CSV y GeoJSON del propio repositorio; no necesita los mosaicos DEM de `02_datos_originales/elevacion`.
4. Dejar visible la atribución al pie de la página. El uso de las teselas públicas de OpenStreetMap está sujeto a su política de uso aceptable; para tráfico alto conviene un proveedor de teselas propio.

## Pruebas

```powershell
& $py -m unittest discover -s tests -v
```

`test_vista_rutas.py` comprueba, con los datos reales: solo rutas elegibles y sin duplicados; ninguna comparación mezcla destinos finales distintos (incluida R006/R022); las llegadas de un mismo destino coinciden (<100 m) y las de destinos distintos no; destino con una sola alternativa; lugar inexistente o sin elegibles; clasificación «en desarrollo» y recomendación bloqueada sin modelo final; perfiles sobre la línea del GeoJSON (menos de 1 m); regreso al punto de inicio y distancia total; circuito cerrado; nombre de acceso de R006 no presentado como verificado; escape de HTML en el visor; GPX sin `<ele>` ni `<time>`.

`test_app_humo.py` ejecuta `app.py` con un Streamlit simulado. **No valida las firmas de la API real de Streamlit**; eso solo se comprueba ejecutando la página.

## Pendiente

- Revisar visualmente la integración descriptiva del índice en escritorio y móvil; las pruebas `AppTest` con Streamlit real ya pasan.
- Verificar el inicio de R006 contra OpenStreetMap o un mapa oficial y corregir el inventario con evidencia.
- Confirmar acceso y condiciones de todas las rutas antes de cualquier recomendación.
- Cerrar las decisiones metodológicas y de acceso antes de plantear niveles finales o recomendaciones; el mínimo de 20 elegibles ya se alcanzó.

## Ejecución real con Streamlit (21 de octubre de 2026)

`tests/test_app_streamlit_real.py` ejecuta `app.py` con el Streamlit real (`AppTest`, versión 1.66.1) y recorre todos los lugares y destinos. Además se abrió la página en vivo (`streamlit run app.py`): cambio de lugar y de destino, botones «Ver en el mapa», visor integrado (`st.iframe`) con mapa base OSM cargado con conexión, perfil y marcador, y botones de descarga. Capturas en `08_evidencias/interfaz_2026-10-21/`. Las teselas de OpenTopoMap («Topográfico») no se comprobaron.

## Actualización metodológica del 23 de octubre

La capa `06_scripts/vista_rutas.py` ya puede leer la clasificación principal Fácil/Moderada/Difícil mediante `dificultad_fisica_estimada()`, sin levantar la puerta de recomendación. La interfaz visible anterior aún corresponde al corte K-means y debe adaptarse siguiendo `prompt_claude_interfaz_plan_final_2026-10-23.md`. El rediseño mostrará una sola categoría pública de dificultad física estimada, ocultará los códigos internos de ruta en la experiencia normal, retirará emojis decorativos y reservará la comparación para los destinos que realmente tienen alternativas. La validación externa de las categorías sigue pendiente.

## Cuándo se habilitarían niveles finales o recomendaciones

La página no muestra niveles hasta que se cumplan TODAS estas condiciones (`vista_rutas.estado_clasificacion`): 20 o más elegibles; archivo `07_resultados/tablas/niveles_esfuerzo_finales.csv` que cubra exactamente esas rutas; y un registro explícito `07_resultados/tablas/validacion_modelo_final.json` con `aprobado: true`, `aprobado_por`, `fecha` (no futura), `version_modelo`, `n_rutas_elegibles` y el `sha256_niveles` exacto del archivo. Alcanzar 20 y crear el CSV no basta; cambiar el archivo después de aprobarlo invalida la validación. Hoy ninguno de los dos archivos existe.

Corte del 21 de octubre tras rehabilitar R001: la suite completa tiene 87 pruebas y pasa en el entorno del proyecto (Streamlit 1.66.1) con TEMP/TMP dentro del proyecto; auditoría 226/226.

**Actualización del 23 de octubre:** el corte vigente es 27 procesadas / 20 elegibles provisionales / 0 habilitadas. La nueva clasificación de tres niveles está integrada en la capa de datos, no todavía en la presentación visual. Las cifras y verificaciones de los cortes anteriores se conservan como historial; deben repetirse después del rediseño.

## Actualización 2026-10-23: interfaz de tres niveles

La página principal (`app.py`; `web/app.py` la ejecuta sin cambios) ya no muestra clases K-means. Lee la
categoría con `vista_rutas.dificultad_fisica_estimada(id_ruta)` (tabla
`07_resultados/tablas/clasificacion_dificultad_fisica_2026-10-23.csv`) y no recalcula nada.

- **Explorar rutas**: filtros por lugar, nombre y dificultad; 20 tarjetas de igual altura (4 columnas en escritorio, 1 en móvil) con nombre, «Dificultad física estimada: X», distancia, ascenso y un aviso solo cuando hay una advertencia de acceso, altitud o trazado. Resultado: 8 Fácil, 10 Moderada, 2 Difícil.
- **Comparar alternativas** (secundaria): solo rutas al mismo destino exacto (Yellow House 3, Yanacocha 2, Mirador Cerro de la Luz 2).
- **Metodología y límites**: regla de esfuerzo, categorías, sensibilidad (6 rutas sensibles, aviso en su detalle) y contrastes K-means/Ward/DBSCAN/HEN solo como contraste metodológico.
- Sin códigos R### ni emojis decorativos. El ingreso con nombre vive solo en `session_state`, no crea una cuenta, no pide contraseña y no se guarda en base de datos. Clima opcional y plegado, con temperatura, precipitación y viento por separado; un fallo de red no afecta la exploración.
- La puerta de recomendación sigue bloqueada.

Verificación entregada por Claude: pruebas con Streamlit simulado y maquetas estáticas E39–E43, que no son capturas de Streamlit real. La comprobación posterior en el entorno local ejecutó la suite completa con Streamlit real (198/198 pruebas) y la auditoría (272/272 controles, sin advertencias ni errores). También se revisó la aplicación en el navegador, incluida una vista de 390 × 844 px, la identificación temporal y el bloque de avisos de Cascada Guarumos. «Acceso y estado» ocupa el ancho principal; altitud y carácter técnico se presentan como tarjetas secundarias y se apilan en móvil sin desbordamiento horizontal. Esta revisión no equivale a una prueba en un teléfono físico ni a una validación con usuarios. Siguen pendientes la revisión por especialistas, la prueba de comprensión con usuarios y las comprobaciones de acceso/campo.

## Ajuste de entrada del 23 de octubre

La visita ahora comienza con un formulario compacto y obligatorio de nombre. Al pulsar «Comenzar», la página saluda y muestra las rutas; no se crea una cuenta ni se guarda el nombre en una base. Se retiraron de la interfaz el aviso «Versión en desarrollo», la lista de validaciones pendientes y los indicadores de estado interno. Esos pendientes siguen documentados en los informes de la tesis.

## Actualización 2026-10-23 (noche): usabilidad y visor

- Bienvenida: tarjeta centrada, se envía con Enter, aviso amable si el nombre está vacío y botón «Cambiar nombre». El nombre solo vive en la sesión (sin cuentas ni base de datos).
- Explorar: cada tarjeta tiene «Ver ruta»; la ficha se abre en lugar de la lista, con «Volver a la lista» y un selector «Cambiar de ruta». Se muestran 12 rutas y un botón para ver las restantes (con filtros se muestran todas las coincidencias). La portada se resumió en una línea de límites.
- Visor: capa «Satélite» (Esri World Imagery, con atribución), tramo recorrido resaltado (ida en naranja, regreso en blanco discontinuo), punto con pulso y opción «Seguir el recorrido» durante la simulación. La lectura dice «altitud» en lugar de «elevación DEM». Se probó una vista 3D con relieve y se descartó por su aspecto poco claro.
- Tema oscuro fijo y color principal azul petróleo (`.streamlit/config.toml`); el cambio de tema requiere reiniciar Streamlit.
- Capturas en Streamlit real: `08_evidencias/E_*streamlit_real_2026-10-23.jpg`.
