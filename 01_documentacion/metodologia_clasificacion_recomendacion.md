# Metodología de clasificación y recomendación de rutas

> **Estado de la página desde el 10/11/2026:** el apartado 16 registra la decisión posterior de mostrar los tres grupos K-means como etiquetas relativas y experimentales. Los apartados 1–15 conservan la evolución histórica, incluido el rechazo científico según C1–C5; las afirmaciones anteriores sobre qué se muestra al público describen el estado previo. Véase `decision_interfaz_kmeans_k3_2026-11-10.md`.

**Fecha de definición:** 2026-10-07
**Estado:** plan inicial histórico. La evaluación reproducida con 20 rutas y la decisión metodológica vigente constan en el apartado 12. Los apartados 1–11 documentan cómo evolucionó la propuesta y no deben citarse como resultados finales.

## 1. Problema que resolverá el sistema

El sistema no intentará predecir si una persona completará una ruta ni inventará una dificultad oficial. Su objetivo será:

1. agrupar alternativas de trekking físicamente parecidas a partir de mediciones objetivas;
2. interpretar esos grupos como niveles relativos de exigencia física;
3. permitir que una persona seleccione un destino y compare las alternativas disponibles;
4. recomendar la alternativa más compatible con sus preferencias y ubicación.

La unidad modelada será la **alternativa de ruta**, no la montaña o destino completo. Si Laguna Verde tuviera tres accesos realmente distintos, los tres compartirían un `id_destino`, pero tendrían tres `id_ruta` y tres perfiles físicos independientes.

## 2. Delimitación temática

El conjunto principal contendrá caminatas, senderos y trekking no técnico dentro de Pichincha. Se excluyen las alternativas que exijan escalada, progresión glaciar o equipo técnico obligatorio. La altura elevada no constituye por sí sola una exclusión, pero obliga a verificar documentalmente el tipo de actividad.

Las rutas dudosas se conservarán para auditoría. No se utilizarán para ajustar el modelo hasta resolver su identidad, geometría o compatibilidad temática.

## 3. Por qué se usará aprendizaje no supervisado

Actualmente no existe una etiqueta externa y confiable de dificultad para cada ruta. Asignar manualmente `fácil`, `moderada` o `difícil` antes del análisis convertiría la conclusión en una decisión subjetiva. Por ello se utilizará aprendizaje **no supervisado**.

### Modelo principal: K-means

K-means formará grupos de rutas semejantes a partir de variables numéricas estandarizadas. Se selecciona como modelo principal porque:

- permite obtener grupos interpretables mediante sus centroides;
- asigna una ruta nueva a un grupo existente mediante `predict`;
- es reproducible si se fija `random_state`;
- funciona bien como primera aproximación cuando las variables son continuas y se controla la escala.

### Validación: agrupamiento jerárquico de Ward

El agrupamiento jerárquico no será un segundo resultado independiente. Se utilizará para comprobar si las relaciones observadas por K-means también aparecen al construir una jerarquía de similitud entre rutas. El dendrograma ayudará a detectar divisiones inestables o rutas atípicas.

### Por qué no se usará Random Forest todavía

Random Forest es supervisado: necesita una etiqueta objetivo confiable para cada observación. En este proyecto todavía no existen suficientes etiquetas verificadas. Podrá evaluarse como trabajo futuro si un experto clasifica un conjunto amplio de rutas o si se recopilan valoraciones consistentes de usuarios.

## 4. Variables candidatas

El conjunto maestro conservará todas las métricas auditables, pero el modelo inicial evaluará estas variables:

- `distancia_total_km`;
- `ascenso_total_m`;
- `elevacion_max_m`;
- `pendiente_media_abs_pct`;
- `pendiente_p95_abs_pct`.

Antes de ajustar el modelo se analizarán correlaciones, distribuciones y valores atípicos. Si dos variables expresan casi la misma información, se conservará la de interpretación más clara para evitar ponderar dos veces el mismo fenómeno.

Las variables se transformarán con `StandardScaler`, porque kilómetros, metros y porcentajes tienen escalas distintas. Sin estandarización, la variable con valores numéricamente mayores dominaría las distancias internas de K-means.

## 5. Selección y validación del número de grupos

Cuando existan suficientes rutas elegibles se compararán, como mínimo, soluciones entre 2 y 5 grupos, respetando que cada grupo contenga varias observaciones. Para cada valor de `k` se documentarán:

- inercia y curva del codo;
- coeficiente de silueta;
- tamaño de cada grupo;
- estabilidad con distintas semillas;
- coherencia física de los centroides;
- concordancia aproximada con la estructura jerárquica de Ward.

El mejor valor no será simplemente el que produzca el mayor indicador matemático. También deberá generar grupos estables, con tamaños utilizables y una interpretación físicamente coherente.

## 6. Interpretación de los grupos

K-means devolverá números de grupo sin significado ordinal. Después del ajuste se calculará el perfil físico de cada centroide. Solo entonces se asignarán nombres comprensibles, por ejemplo:

- exigencia física relativamente baja;
- exigencia física relativamente media;
- exigencia física relativamente alta.

Estas etiquetas serán relativas al conjunto analizado y no equivaldrán a una certificación de seguridad o dificultad técnica.

## 7. Recomendación al usuario

La recomendación será una capa posterior a la clasificación:

1. el usuario inicia una sesión temporal sin base de datos;
2. selecciona un destino o zona;
3. el sistema recupera las alternativas disponibles de ese destino;
4. muestra su grupo de exigencia, distancia, ascenso, perfil y mapa;
5. calcula compatibilidad según preferencias declaradas como esfuerzo deseado, distancia aceptable y cercanía;
6. ordena las alternativas y explica por qué recomienda la primera.

El clima en tiempo real podrá mostrarse como dato informativo cuando se construya la interfaz. No formará parte del entrenamiento, porque cambia con el tiempo y no es una propiedad estable de la ruta.

## 8. Condición mínima antes del entrenamiento final

Después de incorporar R018 se contaban dieciocho rutas procesadas y doce elegibles *provisionales*. El 12 de octubre se excluyeron preventivamente R012 y R014 por identidad y extremos sin confirmar: el conjunto vigente tiene **18 procesadas y 10 elegibles provisionales**. Entrenar un modelo final con esa muestra produciría una clasificación frágil. La meta operativa es reunir al menos **20 alternativas elegibles**, preferiblemente 25 o más, con diversidad suficiente de distancia, desnivel, altura y pendiente. Hasta entonces los análisis de clustering serán exploratorios.

**Actualización del 13 de octubre:** el conteo anterior corresponde al corte previo a R019. Tras incorporar esa ruta, el inventario cuenta **19 rutas procesadas y 11 elegibles provisionales**; faltan **9 elegibles** para la meta operativa de 20. El contraste espacial adicional de R002 respalda parcialmente su trazo, pero no valida el extremo alto, por lo que R002 continúa fuera de la muestra. No se entrenará ni presentará un clasificador final basándose en la cantidad de candidatas procesadas o en una coincidencia espacial parcial.

Se implementó un **ensayo exploratorio** con 11 rutas elegibles provisionales (`ensayo_clustering_exploratorio_2026-10-13.md`). Para evitar dar doble peso a medidas casi equivalentes de pendiente (correlación de Pearson de 0,911 entre media absoluta y p95 en este corte), el primer ensayo usa cuatro variables: distancia, ascenso, elevación máxima y pendiente media absoluta. Incluye sensibilidad sin R011/R013, comparación con Ward y tamaños mínimos de dos rutas por grupo. Los resultados no generan etiquetas de dificultad ni recomendaciones.

El entorno local presentó un error nativo de `threadpoolctl` al ejecutar `sklearn.cluster.KMeans`; también falló una prueba numérica de cinco variables. El ensayo usa temporalmente `scipy.cluster.vq.kmeans2` con semillas explícitas y distancias euclidianas verificables. Esto no cambia la familia del algoritmo, pero **la implementación final y su entorno deben resolverse y verificarse** antes de guardar un modelo para la interfaz.

## 9. Referencias técnicas de implementación

- Scikit-learn, `StandardScaler`: https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html
- Scikit-learn, `KMeans`: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html
- Scikit-learn, análisis de silueta: https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html
- Scikit-learn, `AgglomerativeClustering`: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html

## 10. Estado vigente al 17 de octubre de 2026

Los conteos del apartado 8 son cortes históricos. El conjunto vigente tiene **20 rutas procesadas y 12 elegibles provisionales**; ocho no entran al modelado y faltan ocho elegibles para la meta operativa. La decisión formal del 16 de octubre fue **NO CONGELAR** el inventario. El bloqueo local de scikit-learn quedó resuelto para el ensayo exploratorio configurando `MKL_THREADING_LAYER=SEQUENTIAL` antes de importar NumPy; aún no autoriza un modelo final.

El EDA actualizado del 17 de octubre (`eda_preliminar_12_rutas_2026-10-17.md`) muestra correlación de Spearman de **0,94** entre distancia total y ascenso, concentración de 6/12 rutas en los dos destinos más representados y alertas descriptivas de valores altos de R006. Ninguna alerta estadística se usa para borrar una ruta o asignarle dificultad. Las pruebas exploratorias de K-means/Ward siguen siendo inestables y no producen etiquetas publicables. La próxima decisión metodológica depende de trazados adicionales verificables o de una modificación de alcance aprobada por el tutor.

Como prueba adicional de robustez, el ensayo `ensayo_clustering_exploratorio_sklearn_2026-10-17.md` retira por separado los destinos con varias alternativas elegibles. La asignación de las rutas restantes cambia considerablemente al retirar Pondoña o Yanacocha (ARI 0,096 frente a la base, k=2). Quitar Yanacocha y quitar R011/R013 es exactamente la misma prueba. Los ARI se calculan únicamente sobre rutas comunes; no son una medida de acierto frente a etiquetas verdaderas. Este resultado refuerza el bloqueo de la clasificación final y la necesidad de diversificar la muestra.

La misma revisión prueba el posible doble peso de distancia total y ascenso. Con esta muestra y los filtros de grupos no unitarios, la configuración sin distancia no produjo una partición aceptada; al retirar ascenso, la partición k=2 tuvo ARI **−0,066** frente a la base. Estos resultados no demuestran que una variable sea indispensable ni permiten escoger el subconjunto definitivo: se repetirán al cerrar y diversificar el inventario.

## 11. Corte posterior del 17 de octubre: variante R021

Las cifras del apartado 10 describen el corte anterior a R021. Tras incorporar la variante cartografiada Yellow House por Senderos 1 y 2, el dataset tiene **21 rutas procesadas y 13 elegibles provisionales**; faltan siete para la meta metodológica. La verificación topológica, su perfil y sus límites se documentan en `validacion_r021_yellow_house_2026-10-17.md`. Como comparte destino y acceso con R017/R020, se añade al ensayo de sensibilidad un escenario sin R021. Su inclusión definitiva exige confirmar apertura e independencia práctica; no se publican clases ni recomendaciones con este corte. El EDA vigente es `eda_preliminar_13_rutas_2026-10-17.md` y conserva el corte de doce como histórico.

## 12. Decisión metodológica vigente con 20 rutas (22 de octubre)

El umbral operativo ya se alcanzó: **27 rutas procesadas, 20 elegibles para el análisis y 7 excluidas**. Las 20 observaciones tienen IDs únicos y valores completos; representan **13 destinos exactos**. «Elegible para el análisis» no significa sendero abierto ni apto para cualquier visitante. Los resultados reproducibles se encuentran en `informe_validacion_metodologica_2026-10-22.md`, `contraste_kmeans_dbscan_2026-10-22.md`, `informe_indicador_esfuerzo_2026-10-22.md` y sus tablas de `07_resultados/tablas/`.

### Qué modelos se aplicaron

- **K-means no supervisado:** cuatro variables estandarizadas (distancia total, ascenso total, elevación máxima y pendiente media absoluta), `k=2,3,4`, 50 semillas. La solución `k=2` tiene silueta **0,448**, grupos **4/16**, estabilidad entre semillas **ARI=1,00** y coincide con Ward **ARI=1,00**. `k=3` y `k=4` se descartaron por inestabilidad y grupos pequeños.
- **Ward:** contraste jerárquico de la partición, no etiqueta externa de verdad ni prueba de seguridad.
- **DBSCAN:** malla `eps` 0,5–2 y `min_samples` 2–4. En las nueve configuraciones con al menos dos grupos, las cuatro rutas del grupo pequeño de K-means son **ruido**, no un segundo grupo denso. DBSCAN no valida una escala de dificultad ni contradice de modo concluyente a K-means.
- **Random Forest:** no se aplica; es supervisado y no existen etiquetas externas fiables para entrenamiento y evaluación.

### Interpretación y decisión

La partición `k=2` separa esencialmente **ascenso acumulado alto** (R001, R003, R006, R022; mínimo 449 m) del resto (máximo 339 m); el ascenso por sí solo la reproduce. No equivale a dos clases generales de esfuerzo: R020 tiene más índice de esfuerzo que R022, pero está en el grupo de menor ascenso. Duplicar el peso de la altitud cambia la partición a 10/10 (ARI **0,13**). No se presentarán los números de clúster como «fácil/difícil», dificultad técnica ni recomendación.

El resultado principal de **esfuerzo estimado para comparación** es el indicador continuo HEN = distancia total (km)/5 + ascenso total (m)/600. Es una convención de horas-equivalentes derivada de Naismith, **no un tiempo medido ni una predicción calibrada para Pichincha**. La altitud, el carácter técnico y el acceso se muestran por separado. La página permite ordenar alternativas solo si llegan al mismo destino exacto y mostrar el mapa, perfil, métricas, avisos y clima informativo. No se hace una recomendación de seguridad o de «mejor ruta» mientras el acceso de las alternativas no esté corroborado.

Esta es una **conclusión del análisis**, no un entrenamiento que quedó pendiente por falta de rutas: la muestra mínima permitió evaluar K-means y DBSCAN, y la evaluación rechazó la interpretación de sus grupos como niveles completos de dificultad física. Si se exige una salida categórica en un estudio posterior, habrá que definir el constructo y los cortes con fuentes independientes y validarlos fuera de esta misma muestra; no se inventarán umbrales después de observar los grupos.

## 13. Revisión del mismo corte: K-means de esfuerzo físico relativo (22 de octubre)

El apartado 12 conserva el diagnóstico del **modelo inicial de cuatro variables**; no es la última especificación. A petición del estudiante y para responder al objetivo categórico del plan, se ajustó una especificación de K-means centrada en **distancia total y ascenso total**, estandarizadas con igual peso. La altitud y la pendiente se mantienen como contexto/sensibilidad, no como entradas del modelo principal. Esta revisión no se presenta como preregistrada: se hizo después de examinar el resultado inicial, y esa secuencia es una limitación explícita.

Con 20 rutas, k=2 produce **12/8** y silueta **0,5919**; las 50 semillas y Ward coinciden (ARI **1,00**). k=3 alcanza silueta 0,5895 y también es estable entre semillas, pero deja un grupo de 2, por debajo del criterio previo de tamaño mínimo de 3, sin mejorar la separación; k=4 es menos estable. Se asignan las 20 rutas a **dos clases de exigencia física estimada relativa a esta muestra**. La clase de mayor exigencia tiene simultáneamente mayores distancia y ascenso en promedio y rangos observados sin solapamiento con la clase menor. Cuatro rutas largas de ascenso moderado (R017, R019, R020, R021) cambian cuando se duplica el peso del ascenso, se reduce a la mitad el de distancia o se añade pendiente media; deben llevar aviso de sensibilidad.

Este fue el modelo K-means categórico principal en el corte del 22 de octubre, descrito y reproducible en `informe_modelo_kmeans_fisico_2026-10-22.md`. El apartado 14 registra la decisión posterior de mantener las tres categorías previstas en el plan mediante una regla física externa al agrupamiento. K-means y el índice HEN quedan como contrastes y no sustituyen esa regla. Ninguna salida equivale a dificultad técnica, acceso permitido, seguridad o adecuación personal; por ello no activa una recomendación de salida.

## 14. Clasificación principal en tres niveles (23 de octubre de 2026)

Por decisión del estudiante, coherente con la formulación inicial del plan, la salida categórica principal es **Fácil, Moderada y Difícil**. No se fuerza `k=3`: la evaluación de K-means no justificó tres conglomerados robustos y conceptualmente ordenados. En su lugar se adopta una regla explícita inspirada en el componente de cantidad de esfuerzo de MIDE.

Para cada ruta se calcula el componente horizontal como `distancia_total_km / 4 km/h` y el vertical como `ascenso_total_m / 400 m/h + descenso_total_m / 600 m/h`. El tiempo efectivo estimado es el mayor de ambos componentes más la mitad del menor. Se aplican los intervalos de esfuerzo MIDE y se adaptan a las tres categorías del proyecto: nivel 1 (hasta 1 h) = **Fácil**; nivel 2 (más de 1 y hasta 3 h) = **Moderada**; niveles 3 a 5 (más de 3 h) = **Difícil**. La velocidad horizontal de 4 km/h se declara como supuesto porque el inventario no contiene una tipología homogénea de superficie para usar velocidades distintas por tramo.

El resultado base es 8 Fácil, 10 Moderada y 2 Difícil. Se comparan velocidades horizontales de 3 y 5 km/h, desnivel del DEM filtrado y desnivel del perfil raw. Seis rutas cambian de nivel en al menos un escenario (`R003`, `R004`, `R008`, `R019`, `R025`, `R026`); la interfaz debe comunicar esa sensibilidad sin sustituir la categoría base.

Esta es una **clasificación de dificultad física estimada**, no el MIDE completo: no evalúa severidad del medio, orientación ni dificultad de desplazamiento con la información necesaria para dichas escalas. Tampoco evalúa clima actual, acceso, estado del sendero, experiencia personal o seguridad. Requiere validación de contenido por especialistas y prueba de comprensión con usuarios. Método, matriz y parámetros: `clasificacion_dificultad_fisica_tres_niveles_2026-10-23.md` y `07_resultados/tablas/clasificacion_dificultad_fisica_2026-10-23.csv`.

## 15. Evaluación de K-means con k=3 (10 de noviembre de 2026)

Después de fijar la clasificación pública (apartado 14) se evaluó de forma explícita si K-means con k=3 podía producir las tres categorías. El diseño, las variables (distancia total y ascenso total estandarizados, pesos iguales), el orden físico de los grupos y los criterios de aceptación C1–C5 se escribieron antes de ejecutar (`diseno_experimento_kmeans_k3_2026-11-10.md`). Este experimento no sustituye ni modifica los apartados anteriores, que se conservan como cortes históricos; sus resultados están en `informe_kmeans_k3_dificultad_2026-11-10.md`, `07_resultados/tablas/kmeans_k3_*_2026-11-10.csv` y la sección 11 del notebook 05.

**Qué se encontró.** Con las mismas 20 rutas, k=3 forma grupos de **12/6/2** (silueta 0,5895; misma partición en las 50 semillas; ARI con Ward 0,9246). El grupo de dos rutas es R001 y R006. No hay inversiones de esfuerzo estimado entre grupos adyacentes. La partición se mantiene con pesos moderados, con el ascenso de mediana de 5 puntos del DEM, al retirar una ruta cualquiera (salvo cambios menores: sin R001 pasa R022), al retirar R026 y R027 y al conservar una alternativa por destino. Es frágil ante el perfil DEM crudo, usado como prueba de estrés con ruido documentado (cambian R003, R015, R019 y R023), ante pesos extremos (R006 deja el grupo superior) y ante la elección de variables (al añadir la elevación máxima cambian 14 rutas). DBSCAN marca de 3 a 6 rutas como ruido en las configuraciones que forman grupos y no respalda tres grupos estables sobre las 20 rutas.

**Decisión y conclusión.** Según los criterios fijados para este experimento, la decisión es **B** (fallan C3, tamaño mínimo de grupo, y C5, por el escenario de estrés del DEM crudo). La conclusión científica es que k=3 **no está justificado todavía** para sustituir la clasificación pública; no se declara refutado. Un grupo de dos rutas es una debilidad importante, no una prueba de que sea imposible describirlo. Los límites entre grupos son huecos de la muestra (1,39 a 1,89 h y 2,81 a 4,06 h de esfuerzo estimado), no umbrales con significado de esfuerzo.

**Comparación con la regla.** 16 de las 20 rutas coinciden por orden entre los grupos de K-means y los niveles de la regla; R004, R015, R023 y R026, Moderada según la regla, están en el grupo de menor esfuerzo de K-means. La regla no es verdad de terreno, de modo que estas cuatro discrepancias no miden exactitud.

**Por qué la salida pública sigue siendo la regla.** La clasificación pública continúa siendo **8 Fácil, 10 Moderada y 2 Difícil**, producida por la regla física inspirada en el esfuerzo MIDE, porque sus umbrales tienen unidad (horas de marcha efectiva), cada ruta se clasifica sin depender de las demás y la sensibilidad se informa ruta por ruta. K-means no genera esas etiquetas: aporta una descripción de la estructura de las 20 rutas. Para llamar Fácil, Moderada y Difícil a los grupos haría falta evidencia externa (juicios de especialistas o esfuerzo percibido), más rutas de esfuerzo alto, límites con significado de esfuerzo y perfiles DEM verificados.

## 16. Decisión posterior de presentación del prototipo (10 de noviembre de 2026)

Por decisión del estudiante, la página de demostración presenta las asignaciones del experimento K-means k=3 como tres categorías de **esfuerzo relativo y experimental**: 12 Fácil, 6 Moderada y 2 Difícil. El apartado 15 describe el estado anterior y su conclusión científica sigue vigente: los criterios C3 y C5 no se cumplieron. No se ha convertido esa decisión B en una validación positiva. La regla de esfuerzo de los apartados anteriores queda como contraste y como fuente de horas de referencia; no asigna la etiqueta de la página. La justificación, las cuatro discrepancias, las alertas de sensibilidad y los límites para usuarios se documentan en `decision_interfaz_kmeans_k3_2026-11-10.md`.
