# Tesis: clasificación y recomendación de rutas de trekking en Pichincha

Este repositorio construye un conjunto reproducible de rutas de trekking no técnico en Pichincha y una página para explorar y comparar recorridos al mismo destino. Desde el 10 de noviembre, la página muestra tres grupos de **esfuerzo físico relativo** (Fácil, Moderada y Difícil) asignados por **K-means k=3** sobre distancia total y subida acumulada de las 20 rutas. Son etiquetas experimentales relativas a esta muestra; no son una evaluación MIDE, una escala de dificultad técnica, una certificación de seguridad ni una recomendación de salida. La regla de marcha anterior queda como contraste.

## Interfaz de comparación y visor de rutas

La página local `app.py` permite elegir un lugar y un destino exacto, comparar solo las alternativas que llegan a ese mismo destino (elegibles provisionales, no verificadas) y ver cada una sobre un mapa con inicio, llegada, perfil de elevación sincronizado y una **simulación** de ida y regreso. Muestra la clasificación relativa de K-means k=3, avisos por ruta, clima opcional bajo demanda, fuentes y licencias, y descarga en GeoJSON y GPX. **El GPX es un formato de intercambio derivado del trazado: no es una medición GPS de campo ni incluye elevaciones o tiempos inventados.** No hay recomendación de salida ni certificación de seguridad. Detalle en `01_documentacion/decision_interfaz_kmeans_k3_2026-11-10.md`.

```powershell
$pythonProyecto = 'C:\Users\LENOVO\miniforge3\envs\trekking_pichincha\python.exe'
& $pythonProyecto -m streamlit run app.py
```

Abrir la dirección local que imprima Streamlit, normalmente `http://localhost:8501`. Las teselas del mapa necesitan conexión a internet. El clima actual se consulta bajo demanda para la ruta seleccionada y es una estimación de modelo, no una medición de campo. Para publicar en Streamlit Community Cloud usar **`web/app.py`**, que emplea `web/requirements.txt` y evita instalar el entorno completo de investigación; pasos en `01_documentacion/publicacion_y_demo_2026-10-22.md`.

## Estado verificado el 22 de octubre de 2026

- 27 rutas con trazado, perfil de elevación e indicadores físicos; R027 añade el Sendero del Viento en Moraspungo (`01_documentacion/validacion_r027_sendero_viento_2026-10-22.md`). R026 corresponde a Tarabita – Cascada Guarumos y R024/R025 a dos senderos al Mirador Cerro de la Luz.
- 20 elegibles provisionales y 0 habilitadas para recomendación: se alcanzó la meta cuantitativa mínima. El EDA vigente es E38 (20 rutas); E37 y los anteriores son cortes históricos.
- R001 está incluida según I10/E10, con aviso de altitud y T3; R024/R025 conservan advertencias sobre la falta de corroboración independiente del trazado y de confirmación de acceso; R026 exige cruzar una tarabita privada de pago (tarifa y horario por confirmar) y comparte su trazado con R005, que sigue no elegible. Ninguna inclusión certifica seguridad.
- 7 rutas permanecen fuera del modelado mientras se resuelven verificaciones de identidad, geometría o compatibilidad temática. R011 y R013 también requieren confirmar el recorrido turístico completo.
- 0 valores faltantes en las variables candidatas.
- K-means k=3 asigna **12 rutas Fácil, 6 Moderada y 2 Difícil** en sentido relativo a la muestra. Seis rutas cambian de grupo en al menos una de las pruebas de sensibilidad consideradas en la página y muestran ese aviso.
- Los seis notebooks 00–05 tienen salidas guardadas; el 04 se reejecutó con R027 y 27 filas, y el 05 incluye la evaluación del nuevo K-means físico y, desde el 10 de noviembre, el experimento k=3 (sección 11). El 02 contrasta archivos existentes sin sobrescribir trazados.
- **Método categórico mostrado:** K-means k=3 sobre distancia total y ascenso acumulado estandarizados. Los grupos se ordenan por sus centroides y se nombran Fácil, Moderada y Difícil **solo en relación con estas 20 rutas**. La regla de horas inspirada en MIDE, K-means k=2, Ward, DBSCAN y HEN quedan como contrastes metodológicos.
- `01_documentacion/informe_indicador_esfuerzo_2026-10-22.md` evalúa un indicador continuo Naismith de distancia y ascenso como referencia comparativa, sin tiempos medidos, clases ni recomendaciones.
- El hito de cierre del 16 de octubre se resolvió **NO CONGELAR** por muestra insuficiente y verificaciones de fuente pendientes.
- El EDA del 22 de octubre actualiza distribuciones y correlaciones (E38) para 20 rutas. Las alertas descriptivas no implican exclusión automática.
- Los ensayos históricos de cuatro variables mostraron sensibilidad a altitud y muestra; no deben confundirse con el nuevo modelo de dos variables. El nuevo modelo conserva su partición al retirar una ruta, seleccionar una por destino y variar el filtrado DEM; cuatro rutas cambian al variar pesos o añadir pendiente.
- La página permite comparar por destino exacto, mostrar la clase relativa y marcar alternativas que coinciden con límites personales de distancia y ascenso. La recomendación de salida permanece bloqueada por las verificaciones de acceso y seguridad que este análisis no realiza.
- La revisión adicional de Pasochoa, La Mica, Jerusalem, El Pahuma y Pululahua dejó candidatas pendientes de conexión, identidad o acceso. R022 se incorporó provisionalmente desde una instantánea OSM normalizada, contrastada después con el XML exacto archivado el 20 de octubre; aún faltan confirmar la apertura y dos puntos marcados como posibles vados. R023 procede de un XML OSM archivado y una mención municipal de la caminata, pero requiere verificar acceso y condiciones actuales. R021 requiere confirmar independencia práctica y apertura actual.

La clasificación que muestra la página es K-means k=3, un agrupamiento no supervisado. Los nombres Fácil, Moderada y Difícil son una interpretación de esfuerzo relativo, no etiquetas aprendidas de expertos. Ward, DBSCAN y la regla de marcha son contrastes; Random Forest no se utiliza porque no existen etiquetas externas confiables. La validez de contenido con especialistas y la prueba de comprensión con usuarios siguen pendientes.

## Experimento K-means con k=3 (10 de noviembre de 2026)

Se evaluó si K-means con k=3 sobre distancia total y ascenso total podía producir las tres categorías públicas. Los criterios de aceptación se fijaron antes de ejecutar (`01_documentacion/diseno_experimento_kmeans_k3_2026-11-10.md`) y el detalle está en `01_documentacion/informe_kmeans_k3_dificultad_2026-11-10.md` y en la sección 11 del notebook `05_notebooks/05_validacion_metodologica.ipynb`.

- **Hallazgos:** k=3 forma grupos de 12/6/2 rutas, sin inversiones de esfuerzo, con silueta 0,5895 y la misma partición en las 50 semillas. El grupo de dos rutas es R001 y R006. La partición se mantiene con pesos moderados, con el ascenso de mediana de 5 puntos, al retirar una ruta cualquiera y al conservar una alternativa por destino. Es frágil con el perfil DEM crudo (prueba de estrés: cambian R003, R015, R019 y R023) y con pesos extremos, y depende de las variables elegidas. Ward coincide salvo en R022; DBSCAN deja de 3 a 6 rutas como ruido en las configuraciones que forman grupos y no forma tres grupos estables sobre las 20 rutas.
- **Decisión B según los criterios fijados:** fallan C3 (grupo mínimo de 2 rutas) y C5 (estrés del DEM crudo). La conclusión científica es más matizada: k=3 **todavía no justifica sustituir** las categorías públicas, pero tampoco queda refutado.
- **Comparación con la regla anterior:** 16 de las 20 rutas coinciden por orden; R004, R015, R023 y R026 están en el grupo menor de K-means y son Moderada según la regla. La regla no es verdad de terreno, de modo que esto no mide exactitud.
- **Decisión posterior para el prototipo (10/11):** la página muestra los grupos k=3 como categorías **relativas y experimentales**: 12 Fácil, 6 Moderada y 2 Difícil. Esta decisión no cambia los resultados ni los criterios C1–C5 del experimento: la evaluación científica original eligió la opción B. El grupo superior sigue apoyado en dos rutas y el DEM sin filtrar cambia cuatro asignaciones. La regla anterior (8/10/2) se conserva como contraste histórico, no como fuente de las etiquetas de la página. Véase `01_documentacion/decision_interfaz_kmeans_k3_2026-11-10.md`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `01_documentacion` | metodología, inventario, cronograma, registros de fuentes e informes |
| `02_datos_originales` | descargas OSM y mosaicos Copernicus DEM sin modificar |
| `03_datos_intermedios` | trazados continuos y perfiles altimétricos raw |
| `04_datos_procesados` | perfiles filtrados y variables derivadas |
| `05_notebooks` | verificación, inspección y ampliación documentada |
| `06_scripts` | descarga, procesamiento, análisis y auditoría reproducibles |
| `07_resultados` | tablas maestras, mapas, perfiles y gráficos |
| `08_evidencias` | capturas y figuras numeradas para sustentar el avance |
| `09_referencias` | referencias locales que se incorporen al estudio |

## Archivos principales

- `01_documentacion/inventario_rutas.csv`: catálogo y trazabilidad de cada alternativa.
- `01_documentacion/interfaz_publica_2026-10-21.md`: interfaz de comparación y visor, con reglas, ejecución local y en la nube.
- `01_documentacion/verificacion_rutas_interfaz.csv`: avisos por ruta y estado del nombre de acceso mostrados en la interfaz.
- `07_resultados/tablas/dataset_clasificacion_rutas.csv`: conjunto maestro con variables físicas.
- `07_resultados/tablas/auditoria_dataset_clasificacion.csv`: elegibilidad y acciones pendientes por ruta.
- `07_resultados/tablas/diagnostico_preparacion_modelo.csv`: puerta de control previa al entrenamiento final.
- `01_documentacion/metodologia_clasificacion_recomendacion.md`: justificación del método.
- `01_documentacion/clasificacion_dificultad_fisica_tres_niveles_2026-10-23.md`: definición, resultados, sensibilidad y límites de Fácil/Moderada/Difícil.
- `06_scripts/clasificar_dificultad_fisica.py`: generación reproducible de la clasificación física estimada.
- `06_scripts/evaluar_kmeans_k3_dificultad.py`: experimento K-means k=3 (10 de noviembre de 2026); escribe `07_resultados/tablas/kmeans_k3_*_2026-11-10.csv` y el JSON de parámetros. Desde la decisión posterior del 10/11, sus asignaciones se muestran en la página como grupos relativos experimentales.
- `01_documentacion/diseno_experimento_kmeans_k3_2026-11-10.md` e `informe_kmeans_k3_dificultad_2026-11-10.md`: diseño con criterios a priori, resultados, decisión B e interpretación.
- `07_resultados/tablas/clasificacion_dificultad_fisica_2026-10-23.csv`: matriz completa de asignación de las 20 rutas.
- `01_documentacion/cronograma_2026-10-07_a_2026-10-27.md`: calendario y estado actualizado.
- `01_documentacion/informe_auditoria_integridad_2026-10-22.md`: auditoría vigente del repositorio.
- `01_documentacion/revision_integral_2026-10-19.md`: balance de pruebas, notebooks, búsqueda de candidatas y bloqueos metodológicos.
- `01_documentacion/cribado_pasochoa_2026-10-19.md`: contraste de seis senderos documentados y límites de las trazas públicas halladas.
- `01_documentacion/cribado_nuevos_senderos_2026-10-21.md`: contraste reciente de La Piragua, Humboldt, Kimsa, Vilatuña y Bellavista; ninguno infla el conteo.
- `01_documentacion/eda_preliminar_20_rutas_2026-10-22.md`: análisis exploratorio vigente sin clasificación final.
- `01_documentacion/decision_cierre_inventario_2026-10-16.md`: decisión formal del hito y condiciones para continuar.
- `01_documentacion/ensayo_clustering_exploratorio_sklearn_2026-10-15.md`: agrupamiento exploratorio y pruebas de sensibilidad con 12 rutas.
- `01_documentacion/ensayo_clustering_exploratorio_sklearn_2026-10-17.md`: sensibilidad adicional a destinos representados y a R006.
- `01_documentacion/ensayo_clustering_exploratorio_sklearn_2026-10-17_r022.md`: nuevo ensayo con 14 rutas y sensibilidad sin R022; conserva el corte anterior.
- `01_documentacion/cribado_alternativas_2026-10-17.md`: fuentes y límites de nuevos senderos candidatos.
- `06_scripts/procesar_r022_ilalo.py`: construcción reproducible de R022 desde la instantánea normalizada y fijada por SHA-256; `06_scripts/descargar_r022_ilalo.py` y `06_scripts/contrastar_r022_xml_snapshot.py` descargan y contrastan el XML exacto ya archivado.
- `01_documentacion/validacion_r022_ilalo_2026-10-17.md`: trazabilidad, resultados DEM y límites de R022.
- `01_documentacion/diseno_comparador_recomendacion_2026-10-17.md`: contrato y puertas para la futura recomendación.
- `01_documentacion/preparacion_cierre_inventario_2026-10-21.md`: control espacial vigente y decisión de no congelar.
- `01_documentacion/diagnostico_yanacocha_2026-10-11.md`: contactos entre vías y contraste de longitudes R011–R014.
- `01_documentacion/verificacion_fuente_yanacocha_2026-10-12.md`: interpretación y procedencia de E27.
- `01_documentacion/decision_exclusion_r012_r014_2026-10-12.md`: decisión reversible y efecto en la muestra.
- `01_documentacion/evaluacion_laguna_verde_2026-10-12.md`: cribado de las dos variantes oficiales aún sin geometría verificable.
- `01_documentacion/preparacion_cierre_inventario_2026-10-16.md`: control de la puerta del 16 de octubre y revisión de solapamientos.
- `01_documentacion/validacion_r020_yellow_house_2026-10-14.md`: topología, procedencia y límites de la nueva variante.
- `01_documentacion/validacion_r021_yellow_house_2026-10-17.md`: construcción y límites de la variante más reciente.
- `01_documentacion/prioridades_lotes_13_16_2026-10-12.md`: orden de trabajo y condiciones de aceptación de las candidatas restantes.
- `01_documentacion/revision_tematica_r001_r007_2026-10-12.md`: compatibilidad de los dos trazados de cumbre.

## Entorno

El entorno se declara en `environment.yml`. En el equipo de desarrollo se utiliza:

```powershell
C:\Users\LENOVO\miniforge3\envs\trekking_pichincha\python.exe
```

## Reproducir verificaciones actuales

Desde la raíz del proyecto:

```powershell
$pythonProyecto = 'C:\Users\LENOVO\miniforge3\envs\trekking_pichincha\python.exe'
& $pythonProyecto 06_scripts/preparar_dataset_clasificacion.py
& $pythonProyecto 06_scripts/auditar_integridad_proyecto.py --fecha 2026-10-22
& $pythonProyecto 06_scripts/verificar_preparacion_modelo.py --fecha 2026-10-22
& $pythonProyecto 06_scripts/auditar_cierre_inventario.py --fecha 2026-10-22
```

Los seis notebooks 00–05 tienen salidas registradas. El de ampliación contiene el control vigente de integridad y de muestra. Para actualizar sus resultados sin repetir extracciones:

```powershell
& $pythonProyecto 06_scripts/ejecutar_notebooks_lectura.py
Push-Location 05_notebooks
& $pythonProyecto ..\06_scripts\ejecutar_notebook_python_puro.py .\05_validacion_metodologica.ipynb
Pop-Location
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
& $pythonProyecto -m unittest discover -s tests -v
```

`02_inspeccion_trazados_piloto.ipynb` conserva el análisis histórico, pero sus 11 celdas de código son ahora de lectura y el primer comando actualiza sus salidas sin volver a escribir GeoJSON. El notebook 05 vuelve a generar tablas y figuras metodológicas; por eso se ejecuta de forma explícita desde su carpeta. El resumen vigente de las 27 rutas está en `05_notebooks/04_ampliacion_rutas.ipynb`; la evaluación K-means vigente está en `05_notebooks/05_validacion_metodologica.ipynb`.

El gráfico exploratorio se guarda como una instantánea numerada. E25, E28 y E31–E37 son cortes históricos frente al dataset actual de 20 elegibles, representado en E38. E38 se generó mediante:

```powershell
python 06_scripts/generar_eda_preliminar.py --fecha 2026-10-22 --evidencia E38 --rutas-esperadas 20
```

En Windows el generador fija `MKL_THREADING_LAYER=SEQUENTIAL` antes de importar NumPy/Matplotlib. También puede ser necesario que `Library\\bin` del entorno Miniforge esté al inicio de `PATH`. El generador impide sobrescribir una instantánea ya creada: para una muestra posterior hay que elegir otra fecha y otro código de evidencia. Para reproducir E38 sin tocar el archivo conservado, usar una copia del repositorio.

El contraste K-means se reproduce con:

```powershell
& $pythonProyecto 06_scripts/evaluar_kmeans_esfuerzo.py --fecha 2026-10-22
```

El experimento K-means k=3 (contraste exploratorio, sin tocar los resultados anteriores) se reproduce con:

```powershell
& $pythonProyecto 06_scripts/evaluar_kmeans_k3_dificultad.py --fecha 2026-11-10
& $pythonProyecto -m unittest tests.test_evaluar_kmeans_k3_dificultad -v
```

La clasificación principal de tres niveles se reproduce con:

```powershell
& $pythonProyecto 06_scripts/clasificar_dificultad_fisica.py --fecha 2026-10-23
```

## Siguiente hito

Las 20 rutas y la clasificación reproducible en tres grupos están completadas como prototipo. El siguiente hito es contrastar el significado de Fácil, Moderada y Difícil con especialistas y probar la comprensión con usuarios. Siguen pendientes verificaciones de campo o del administrador para varios accesos; la interfaz no convierte el grupo físico relativo en recomendación de salida o garantía de seguridad.
