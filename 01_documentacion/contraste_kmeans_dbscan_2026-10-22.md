# Contraste directo K-means–DBSCAN (20 rutas)

**Estado:** comprobación exploratoria; no valida clases de esfuerzo ni recomendaciones.

Se cruzaron por `id_ruta` las asignaciones `base_4_variables`, `k=2` de `07_resultados/tablas/grupos_exploratorios_sklearn_2026-10-22_r027.csv` con `07_resultados/tablas/grupos_dbscan_exploratorio_2026-10-22_r027.csv`. Ambos ensayos usan las mismas 20 rutas y cuatro variables estandarizadas. Los números de grupo son arbitrarios.

| DBSCAN (`eps`, `min_samples`) | Rutas agrupadas | Grupos DBSCAN | Rutas del grupo minoritario de K-means tratadas como ruido |
|---|---:|---:|---|
| 1,0; 2 | 15/20 | 3 | R001, R003, R006, R022 |
| 1,0; 3 | 13/20 | 2 | R001, R003, R006, R022 |
| 1,25; 2 o 3 | 15/20 | 2 | R001, R003, R006, R022 |
| 1,5; 2 o 3 | 16/20 | 1 | R001, R003, R006, R022 |
| 2,0; 2 o 3 | 19/20 | 1 | R001 |

En los parámetros que producen dos o tres grupos DBSCAN, **las cuatro rutas del grupo minoritario de K-means son ruido**. Entre las rutas no ruido queda un solo grupo de K-means; por eso el ARI no es una comparación informativa de las dos particiones y el programa lo marca como no comparable. DBSCAN subdivide el grupo grande, sin reproducir la separación 4/16. Con `eps` más alto casi todas las rutas se integran en un único grupo DBSCAN. Por tanto, DBSCAN **no confirma** la partición `k=2`; muestra que esas cuatro rutas son puntos relativamente aislados bajo el criterio de densidad probado. `-1` no significa dificultad ni peligro.

La silueta DBSCAN se calcula excluyendo el ruido; no es directamente comparable con la silueta K-means sobre las 20 rutas. Esta discrepancia requiere examinar las variables y el significado físico del grupo minoritario antes de publicar niveles. Ward sí coincide con K-means en el escenario base, pero ambos favorecen particiones compactas y esa coincidencia tampoco prueba la interpretación como esfuerzo.

**Siguiente comprobación:** caracterizar las cuatro rutas y los centroides en unidades originales, analizar el peso de altitud y redundancia distancia–ascenso, y documentar sensibilidad a rutas inciertas. Mantener cerrada la compuerta de recomendación hasta tomar una decisión metodológica interna reproducible.
