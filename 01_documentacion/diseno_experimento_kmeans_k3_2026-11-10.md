# Diseño del experimento K-means k=3 (escrito antes de ejecutarlo)

**Fecha:** 10 de noviembre de 2026. **Pregunta:** ¿puede K-means con k=3 formar tres grupos físicos coherentes y suficientemente estables como para sustentar los nombres Fácil, Moderada y Difícil, en lugar de la regla de esfuerzo adaptada de MIDE? Este documento fija variables, escalado, configuraciones y criterios de aceptación **antes** de generar las salidas del experimento. No modifica la clasificación publicada ni la historia del proyecto: hoy K-means es un contraste exploratorio y la regla de tres niveles es la clasificación pública.

## 1. Muestra
- Exactamente las rutas con `estado_modelado == "elegible_actual"` en `dataset_clasificacion_rutas.csv`. Se comprueba el conteo: 27 procesadas, 20 elegibles, 7 no elegibles. Los mismos 20 IDs se usan en todas las configuraciones principales (k=2, 3 y 4) y deben coincidir con las 20 de `clasificacion_dificultad_fisica_2026-10-23.csv`.
- Limitación reconocida: muestra intencional, 13 identificadores de destino y 16 destinos exactos; hay alternativas relacionadas (Yellow House ×3; extremo común de Yanacocha ×2; Mirador Cerro de la Luz ×2; R006 y R022 en el mismo cerro). Las observaciones no son independientes y la silueta y la estabilidad pueden sobrestimar la separación real.

## 2. Variables y escalado (configuración principal)
- `distancia_total_km` y `ascenso_total_m` del recorrido completo. Se mantienen porque describen cuánto se camina y cuánto se sube, que es la base física del esfuerzo.
- Estandarización z-score con desviación poblacional (ddof=0), igual que el modelo del 22 de octubre; pesos iguales; distancia euclídea en el espacio estandarizado (la que usa K-means).
- Reconocimiento explícito: distancia y ascenso están correlacionadas (se reporta Pearson y Spearman sobre las 20 rutas). Con dos variables muy correlacionadas, los grupos se alinean sobre un eje dominante de "tamaño del recorrido"; esto favorece la interpretabilidad pero reduce la información independiente.
- Variables adicionales solo como sensibilidad justificada, no como alternativa para obtener tres grupos: (a) + pendiente media absoluta (más sensible al ruido del DEM); (b) + elevación máxima (contexto de exposición, no trabajo acumulado). Si alguna produce otra partición, se reporta tal cual.

## 3. Configuración del algoritmo
- `sklearn.cluster.KMeans`, k-means++, `n_init=10`, semillas 0 a 49; se conserva el ajuste de menor inercia (desempate por semilla menor). k = 2, 3 y 4.
- Se guardan: IDs, variables, media y desviación del escalador, semillas, `n_init`, centroides estandarizados y en unidades originales, inercia, silueta, tamaños y asignación por ruta.
- Orden físico de los grupos de k=3: por la **suma de las coordenadas estandarizadas del centroide** (distancia z + ascenso z), una medida que usa solo las dos variables del modelo y no la regla MIDE. Los índices internos 0/1/2 no significan Fácil/Moderada/Difícil; los grupos se denominan "G1 menor", "G2 intermedio" y "G3 mayor esfuerzo relativo en esta muestra".

## 4. Descripción de grupos e inversiones
- Para cada grupo de k=3: n, rangos, medianas y medias de distancia, ascenso y esfuerzo estimado (horas de marcha efectiva de la regla adaptada, calculadas con la función del proyecto; se usan solo como medida descriptiva independiente del algoritmo, no como etiqueta).
- Inversión: par de rutas (i, j) con i en un grupo de menor orden que j y esfuerzo estimado de i mayor que el de j. Se cuentan y se listan; también se reporta el solapamiento de rangos entre grupos adyacentes para distancia, ascenso y esfuerzo.
- Casos fronteriza: silueta individual y margen entre el centroide más cercano y el segundo (en el espacio estandarizado). Se marcan las rutas con silueta individual < 0,35 o margen relativo < 0,25, umbrales fijados aquí antes de ver resultados. Se examinan por separado R001, R003, R006, R017, R019, R020, R021 y R022.

## 5. Robustez
1. Semillas: ARI mínimo entre las 50 semillas contra el ajuste elegido.
2. Pesos: moderados (distancia ×0,8 o ×1,25) y de estrés (×0,5 o ×2), ambos reportados por separado.
3. Ascenso con alternativas de filtrado DEM: mediana de 3 (base), mediana de 5 y perfil crudo (`indicador_dem_perfiles_2026-10-22.csv`).
4. Retirada de una ruta cada vez (20 escenarios) y de R026 y R027 juntas.
5. Una alternativa por destino: por `id_destino` (13 rutas) y por destino exacto de la interfaz (16 rutas), eligiendo la más corta o la más larga.
6. Ward con k=3 sobre el mismo espacio.
7. DBSCAN sobre el mismo espacio y la misma malla del 22 de octubre; se reportan por separado número de grupos, rutas ruido y cobertura. El ARI con DBSCAN se calcula solo sobre rutas no ruido y se etiqueta como tal; no es acuerdo sobre las 20. Se informa además el ARI tratando el ruido como un grupo, solo como lectura conservadora.
- ARI entre particiones de rutas comunes: en retiradas y submuestras solo sobre las rutas presentes en ambas. Los fallos de ejecución se registran en la salida, no se omiten.

## 6. Criterios de aceptación fijados a priori (para la decisión A/B/C)
- **C1 Estabilidad entre semillas:** ARI mínimo ≥ 0,95.
- **C2 Cohesión:** silueta de k=3 ≥ 0,50 y no inferior en más de 0,05 a la de k=2.
- **C3 Tamaño:** cada grupo con ≥ 3 rutas (criterio previo del proyecto). Un grupo menor solo se acepta con justificación física explícita.
- **C4 Coherencia física:** sin inversiones de esfuerzo estimado entre grupos de orden adyacente y sin solapamiento de rangos del esfuerzo estimado entre grupos adyacentes.
- **C5 Robustez:** ARI ≥ 0,80 en pesos moderados, en las alternativas de DEM, y en al menos el 90 % de las retiradas de una ruta; además ARI ≥ 0,80 al conservar una alternativa por destino.
- **Decisión:** **A** si cumple C1–C5. **B** si falla C4 o si fallan dos o más criterios. **C** en el resto de casos (evidencia ambigua: un solo criterio no esencial en falla). La silueta, Ward y DBSCAN son evidencia interna sobre la estructura de estas 20 rutas, **no** validación externa de la dificultad percibida por personas, y la regla MIDE adaptada no es verdad de terreno.

## 7. Comparación con la regla vigente
- Matriz 3×3 entre los grupos ordenados de K-means y los niveles 8/10/2 de la regla, y tabla de rutas discrepantes con sus medidas. Se informa el ARI y la correlación de rangos como descripción de concordancia; **no se calcula exactitud**. La coincidencia entre grupo e nivel por orden es solo una convención para leer la matriz.

## 8. Asignación de una ruta nueva
- Si el resultado lo justifica, se guardan escalador y centroides y se asigna la ruta al centroide más cercano en el espacio estandarizado. La función se prueba reproduciendo las 20 asignaciones y es válida solo para rutas calculadas con el mismo procedimiento; las nuevas rutas que caigan lejos de todos los centroides (fuera del rango de entrenamiento) deben marcarse como extrapolación.
