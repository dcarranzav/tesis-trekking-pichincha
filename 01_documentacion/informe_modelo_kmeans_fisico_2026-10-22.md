# Clasificación relativa de dificultad física estimada con K-means

> **Estado desde el 23 de octubre de 2026:** este análisis se conserva como contraste exploratorio. La clasificación principal del proyecto es la regla de tres niveles Fácil/Moderada/Difícil documentada en `clasificacion_dificultad_fisica_tres_niveles_2026-10-23.md`. K-means no debe mostrarse como una segunda clasificación pública.

**Fecha:** 22 de octubre de 2026. **Muestra:** 20 rutas elegibles de 27 procesadas. **Unidad de análisis:** ruta de ida y vuelta completa o circuito completo, con indicadores calculados por el mismo proceso. Esta es la clasificación no supervisada solicitada por el plan de titulación; es **relativa a las rutas estudiadas**, no una escala universal ni una evaluación de seguridad.

## 1. Definición del resultado antes de poner nombres

Se estima solo la **exigencia física del recorrido**. Se usan `distancia_total_km` y `ascenso_total_m` porque describen cuánto se camina y cuánto se sube; ambas se estandarizan con media 0 y desviación estándar 1 para que las unidades no determinen el grupo. El peso de partida de ambas es igual. Se excluye `elevacion_max_m` del ajuste: la altura es un contexto fisiológico importante, pero no una medida directa de trabajo acumulado y debe figurar como advertencia separada. La pendiente se informa aparte porque depende más del muestreo y ruido del DEM; su inclusión se evalúa como sensibilidad, no se oculta.

El algoritmo es `scikit-learn KMeans` con inicialización k-means++, `n_init=10`, 50 semillas (0–49) y selección de la menor inercia. En Windows el proceso fija `MKL_THREADING_LAYER=SEQUENTIAL` y `OMP_NUM_THREADS=1` antes de importar NumPy para evitar un fallo nativo de introspección de hilos (0xC06D007F). Los parámetros de estandarización y los centroides se guardan para reproducir y asignar una nueva ruta procesada de la misma forma. No se ajustó el modelo con etiquetas turísticas.

Se comparan k=2, 3 y 4 por silueta, tamaño de grupo, estabilidad entre semillas y concordancia con Ward. DBSCAN sigue siendo contraste, no el clasificador principal. Esta elección de variables se hizo tras ensayos sobre la misma muestra: **no es preregistración ni validación externa**. El objetivo es hacer explícita y evaluable la decisión metodológica.

## 2. Selección de k y significado de los grupos

| k | Silueta | Tamaños | ARI mínimo entre 50 semillas | ARI con Ward |
|---:|---:|---|---:|---:|
| **2** | **0,5919** | **12 / 8** | **1,000** | **1,000** |
| 3 | 0,5895 | 12 / 6 / 2 | 1,000 | 0,9246 |
| 4 | 0,4354 | 7 / 6 / 5 / 2 | 0,5111 | 0,5111 |

Se elige **k=2**: k=3 es también estable entre semillas, pero su silueta no mejora, deja un grupo de solo dos rutas y su concordancia con Ward es menor; el criterio previo de tamaño mínimo de grupo (3 rutas) lo descarta. k=4 reduce la silueta y la estabilidad. Dos grupos no se eligen para prometer «fácil y difícil», sino para obtener una partición parsimoniosa y defendible en estas variables.

| Clase relativa | n | Distancia media (rango), km | Ascenso medio (rango), m | Rutas |
|---|---:|---|---|---|
| **1 · Menor exigencia física estimada en esta muestra** | 12 | 1,76 (0,52–3,34) | 121 (20–239) | R004, R008, R011, R013, R015, R016, R018, R023, R024, R025, R026, R027 |
| **2 · Mayor exigencia física estimada en esta muestra** | 8 | 6,16 (4,36–9,61) | 479 (280–825) | R001, R003, R006, R017, R019, R020, R021, R022 |

Los dos indicadores del modelo son mayores en promedio y no se solapan en sus rangos observados entre estas dos clases. **Eso permite el nombre relativo**, pero no determina que una ruta de clase 1 sea apropiada para principiantes ni que una de clase 2 sea técnica o peligrosa. Altitud, acceso, estado del sendero y carácter técnico siguen en campos independientes.

## 3. Sensibilidad y casos que deben llevar aviso

- Retirar cualquiera de las 20 rutas, incluidos R026 y R027: ARI 1,00 sobre las rutas restantes.
- Conservar una sola alternativa por destino exacto, tanto la más corta como la más larga: ARI 1,00 entre las 13 rutas comunes.
- Recalcular ascenso con mediana de 5 puntos o perfil crudo: ARI 1,00.
- Duplicar el peso de distancia o reducir a la mitad el de ascenso: ARI 1,00.
- **Duplicar el peso de ascenso, reducir a la mitad el de distancia o añadir pendiente media:** ARI 0,3286. Cambian **R017, R019, R020 y R021**, rutas relativamente largas cuyo ascenso es moderado. Son los cuatro casos sensibles, y la tabla los identifica ruta por ruta.

La sensibilidad de cuatro rutas **no se esconde**: la clase base se conserva como asignación del modelo declarado, acompañada por «sensible a ponderación/variables». Es posible revisar escenarios en `modelo_kmeans_fisico_sensibilidad_2026-10-22.csv`. La estabilidad interna no mide exactitud frente al esfuerzo experimentado por personas, ya que no contamos con etiquetas independientes ni mediciones de campo.

## 4. Resultado frente al plan de tesis y la página

### Contraste DBSCAN sobre las mismas dos variables

La malla exploratoria usa `eps` 0,3–1,5 y `min_samples` 2–4 sobre **las mismas dos variables estandarizadas**. Por ejemplo, con `eps=0,5` y `min_samples=3` DBSCAN forma dos grupos entre **16 rutas**, considera ruido a **R001, R003, R006 y R022** y coincide con K-means en las 16 restantes (ARI 1,00 **solo entre las no ruido**). Esto muestra una estructura compatible en el subconjunto denso, pero **no valida las 20 etiquetas**: cuatro rutas de mayor ascenso quedan sin grupo DBSCAN. La tabla `modelo_kmeans_fisico_dbscan_2026-10-22.csv` reporta por separado número de grupos, ruido y cobertura para no confundir acuerdo parcial con exactitud total.

### Comunicación del resultado

El plan pide categorías explicables y prueba de sensibilidad: aquí se entregan **20 asignaciones**, dos categorías relativas, variables, escalado, centroides guardados, criterios de elección y casos sensibles. La interpretación pública correcta es **«exigencia física estimada menor/mayor respecto a estas 20 rutas»**, nunca «ruta segura», «ruta adecuada para ti» o dificultad técnica. El índice continuo HEN puede coexistir como lectura detallada, pero no reemplaza esta clasificación ni se utiliza como etiqueta de entrenamiento.

La página debe mostrar la categoría y su aviso de sensibilidad sin convertirla en recomendación operativa. Las advertencias de R001 (alta montaña/T3) y de acceso siguen separadas. Comparar alternativas en la página sigue exigiendo el **mismo destino exacto**, aunque la categoría se ajustó globalmente sobre las 20 rutas. Ninguna ruta queda habilitada automáticamente para recomendar una salida.

## 5. Reproducción

`python 06_scripts/evaluar_kmeans_esfuerzo.py --fecha 2026-10-22`

Salidas: `07_resultados/tablas/modelo_kmeans_fisico_{resumen,sensibilidad,asignaciones,dbscan}_2026-10-22.csv` y `modelo_kmeans_fisico_parametros_2026-10-22.json`. El JSON conserva variables, media, desviación, centroides, IDs de entrenamiento y SHA-256 del dataset. Las pruebas de regresión recomputan las asignaciones de las 20 rutas a partir de esos parámetros.

**Límites restantes:** muestra intencional pequeña (20 rutas, 13 destinos) y recorridos parcialmente solapados; DEM de 30 m; ninguna medida externa de esfuerzo percibido; el supuesto de que distancia y ascenso capturan solo una parte de la dificultad física. La categorización es un resultado analítico del conjunto estudiado, no una certificación universal.
