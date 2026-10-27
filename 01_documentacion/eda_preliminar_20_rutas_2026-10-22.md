# Análisis exploratorio preliminar (2026-10-22)

## Alcance

Se analizaron **20 rutas elegibles** de 27 rutas procesadas. Este documento no presenta una clasificación final ni entrena K-means. Su objetivo es anticipar problemas de escala, redundancia y valores extremos antes de cerrar el inventario.

## Resumen de variables

| Variable | Mínimo | Mediana | Máximo |
|---|---:|---:|---:|
| Distancia total (km) | 0.52 | 2.85 | 9.61 |
| Ascenso total (m) | 19.66 | 198.12 | 824.84 |
| Elevación máxima (m) | 1284.22 | 2556.56 | 4678.57 |
| Pendiente media abs. (%) | 5.36 | 12.80 | 31.26 |
| Pendiente p95 abs. (%) | 13.09 | 42.89 | 83.92 |

## Hallazgos provisionales

- La mayor correlación absoluta observada es **0.93** entre `distancia_total_km` y `ascenso_total_m`. Debe revisarse nuevamente con el inventario completo para decidir si ambas variables permanecen en el modelo.
- Las escalas son muy distintas: kilómetros, metros y porcentajes. Se confirma la necesidad de aplicar `StandardScaler` antes de K-means.
- Las rutas cortas de reservas y los ascensos de mayor desnivel amplían el rango físico. Esa diversidad es útil, pero exige revisar la estabilidad de los grupos y no interpretar el número de clúster como una dificultad oficial.
- 7 de las 20 rutas provienen de los dos lugares amplios (`id_destino`) con más rutas; un mismo lugar puede contener llegadas distintas. Esa concentración puede influir en los grupos; se revisará la diversidad geográfica antes del ajuste final.
- No se eliminó ninguna observación en esta etapa. La regla de Tukey (1,5 × rango intercuartílico) solo señala valores para revisión.

## Detección descriptiva de valores atípicos

| Ruta | Variable | Valor |
|---|---|---:|
| R001 | Ascenso total (m) | 824.84 |
| R006 | Ascenso total (m) | 817.83 |
| R006 | Pendiente media abs. (%) | 31.26 |

Antes de cualquier exclusión se revisarán la fuente del trazado, el perfil y la plausibilidad física. Con esta muestra pequeña, los cuartiles son inestables.

## Próximo uso

Al cerrar el inventario se volverá a ejecutar este análisis con al menos 20 rutas elegibles. Después se compararán soluciones K-means para varios valores de `k`, estabilidad por semillas y validación jerárquica de Ward.

Figura reproducible: `07_resultados/graficos/eda_preliminar_variables_20_rutas_2026-10-22.svg`.
Evidencia: `08_evidencias/E38_eda_preliminar_20_rutas_2026-10-22.png`.
