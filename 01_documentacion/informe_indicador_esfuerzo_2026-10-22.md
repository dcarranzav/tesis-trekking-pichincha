# Indicador continuo de esfuerzo de referencia (distancia y ascenso)

**Fecha:** 2026-10-22. **Estado:** propuesta metodológica para decisión compartida, **no conectada a la página**. No crea clases «fácil/difícil», no habilita recomendaciones y no escribe `niveles_esfuerzo_finales.csv` ni `validacion_modelo_final.json`.

Reproducir: `python 06_scripts/calcular_indicador_esfuerzo.py --fecha 2026-10-22` (tablas `07_resultados/tablas/indicador_*_2026-10-22.csv|json`, figura `07_resultados/figuras/indicador_esfuerzo_2026-10-22.png`, pruebas `tests/test_indicador_esfuerzo.py`, notebook `05_validacion_metodologica.ipynb`, sección 8). La corrida original se hizo en el espacio de trabajo remoto (scikit-learn 1.9.1, pandas 3.0.5). Se repitió en el entorno local del proyecto el 2026-10-22: notebook 05 con 16/16 celdas de código ejecutadas y 0 errores; suite completa 128/128; auditoría 267/267, sin advertencias ni errores.

## 1. Definición

**HEN = distancia_total_km / 5 + ascenso_total_m / 600** (regla de Naismith: 5 km/h y 600 m de ascenso por hora).

La formulación métrica y sus límites se describen en [Wood et al., *PLOS ONE* (2023)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0295848): sirve como referencia comparativa, pero no captura bien descenso, terreno, obstrucciones ni factores personales. Su aplicación a Pichincha no constituye calibración local.

- Se define **a priori**, con constantes de la literatura, sin ajustarlas a las 20 rutas ni a etiquetas de portales.
- Unidad: **horas-equivalentes de referencia**. Son estimadas, **no tiempos medidos** ni pronósticos para una persona; no incluyen pausas, carga, estado del sendero, clima, técnica ni la altitud.
- Entradas: `distancia_total_km` y `ascenso_total_m` del dataset. Para `ida_y_vuelta`, `distancia_total_km` es el doble del trazado y `ascenso_total_m` es subida + bajada de un sentido (= ascenso total del recorrido completo); para `circular`, una sola vuelta. El script vuelve a calcular el ascenso desde cada perfil procesado y comprueba que coincide con el dataset (|Δ| < 0,5 m en las 20).
- **La altitud no entra en la fórmula.** `elevacion_max_m` se conserva como columna de advertencia separada (`altitud_maxima_advertencia_m`). El Spearman entre HEN y altitud máxima es 0,18: son ejes distintos.
- El descenso no se penaliza ni se premia (la regla clásica solo cuenta subida); se documenta como límite.

## 2. Resultado (orden continuo, sin cortes)

| Pos. | Ruta | Destino | Dist. total (km) | Ascenso (m) | HEN (h) | HEN con ascenso mediana-3 → crudo (h) | Pos. Tobler | Rango de posición en sensibilidades | Altitud máx. (advertencia, m) |
|---:|---|---|---:|---:|---:|---|---:|---|---:|
| 1 | R001 | D001 | 9,61 | 825 | 3,30 | 3,30 → 3,69 | 2 | 1 | 4679 |
| 2 | R006 | D006 | 5,23 | 818 | 2,41 | 2,41 → 2,49 | 1 | 2–3 | 3181 |
| 3 | R003 | D003 | 7,48 | 449 | 2,25 | 2,25 → 2,59 | 3 | 2–3 | 3290 |
| 4 | R020 | D010 | 6,63 | 339 | 1,89 | 1,89 → 2,05 | 5 | 4–5 | 1540 |
| 5 | R022 | D012 | 4,36 | 521 | 1,74 | 1,74 → 1,79 | 4 | 4–6 | 3082 |
| 6 | R021 | D010 | 5,80 | 290 | 1,64 | 1,64 → 1,75 | 7 | 5–7 | 1520 |
| 7 | R017 | D010 | 5,47 | 280 | 1,56 | 1,56 → 1,68 | 8 | 7–8 | 1520 |
| 8 | R019 | D011 | 4,66 | 313 | 1,45 | 1,45 → 2,16 | 6 | 4–8 | 1651 |
| 9 | R015 | D010 | 3,15 | 239 | 1,03 | 1,03 → 1,26 | 9 | 9–10 | 1400 |
| 10 | R023 | D013 | 3,34 | 203 | 1,01 | 1,01 → 1,36 | 11 | 9–10 | 2877 |
| 11 | R026 | D015 | 2,13 | 180 | 0,73 | 0,73 → 1,00 | 12 | 11–13 | 1506 |
| 12 | R025 | D014 | 2,55 | 128 | 0,72 | 0,72 → 0,89 | 13 | 11–13 | 2389 |
| 13 | R004 | D004 | 1,66 | 193 | 0,65 | 0,65 → 0,71 | 10 | 12–13 | 2745 |
| 14 | R008 | D004 | 1,57 | 139 | 0,55 | 0,55 → 0,70 | 14 | 14–15 | 2724 |
| 15 | R016 | D010 | 1,63 | 129 | 0,54 | 0,54 → 0,64 | 15 | 14–15 | 1408 |
| 16 | R027 | D016 | 1,46 | 66 | 0,40 | 0,40 → 0,49 | 17 | 16–17 | 3053 |
| 17 | R013 | D009 | 1,29 | 81 | 0,39 | 0,39 → 0,51 | 16 | 16–17 | 3549 |
| 18 | R024 | D014 | 1,01 | 27 | 0,25 | 0,25 → 0,27 | 19 | 18–19 | 2389 |
| 19 | R011 | D009 | 0,78 | 51 | 0,24 | 0,24 → 0,34 | 18 | 18–19 | 3536 |
| 20 | R018 | D008 | 0,52 | 20 | 0,14 | 0,14 → 0,16 | 20 | 20 | 1284 |

Lectura: se muestran la posición base (1 = mayor esfuerzo estimado) y el rango de posiciones que ocupa la ruta en todas las sensibilidades de las secciones 3 y 4. Los empates prácticos (por ejemplo R015/R023, 1,03 y 1,01 h) no deben interpretarse como diferencia real.

## 3. Sensibilidad a la definición

| Formulación | Spearman con la base |
|---|---:|
| km-esfuerzo (km + m/100) | 0,998 |
| Tobler sobre el perfil (ida y vuelta) | 0,980 |
| solo ascenso | 0,976 |
| solo distancia | 0,968 |
| altitud máxima (ajena al indicador) | 0,184 |

Rejilla de parámetros V ∈ {4; 4,5; 5; 5,5} km/h × R ∈ {300; 400; 500; 600; 800} m/h (20 combinaciones): Spearman mínimo 0,992 frente a la base, ninguna ruta se desplaza más de 1 posición y las cinco primeras rutas son las mismas en 18 de 20 combinaciones. Tobler (que penaliza las pendientes fuertes) intercambia R006 con R001 en la primera posición y sube R004 de la 13.ª a la 10.ª y R019 de la 8.ª a la 6.ª: es un contraste, no una alternativa adoptada.

## 4. Límites y sensibilidad del DEM

- Fuente: Copernicus DEM GLO-30 (resolución ~30 m; paso de muestreo del perfil ~28–30 m, igual a la celda). Es un modelo de superficie: bajo dosel o cerca de construcciones puede incluir la altura de la vegetación o de objetos.
- El ascenso es el indicador más sensible al método: el perfil **crudo** suma entre 1,05 y 2,35 veces el ascenso de la mediana de 3 puntos (mediana 1,52). La mediana de 5 puntos lo reduce (mediana 0,93 de la base). Ni el filtrado de 3 puntos ni el crudo son «el valor verdadero»: el filtro elimina ruido pero también relieve real menor que la celda.
- Efecto sobre el orden (Spearman con la base): mediana-5 0,998 (máximo 1 posición); crudo 0,979 (máximo 4 posiciones, la mayor es R019: de 8.ª a 4.ª con 736 m crudos frente a 313 m filtrados).
- Ruido gaussiano adicional con el mismo filtro (500 simulaciones, semilla 20261022, σ = 1; 2 y 4 m): la posición p05–p95 de cada ruta amplía como máximo 1 posición con σ = 1–2 m y 2 posiciones con σ = 4 m.
- **Consecuencia:** el orden es robusto; los valores absolutos de HEN **no lo son**: con el ascenso crudo, por ejemplo, R001 pasa de 3,30 a 3,69 h y R019 de 1,45 a 2,16 h. Los números deben presentarse como estimaciones de referencia, con su rango, no como duración.
- Otros límites: n = 20 rutas y 13 destinos; alternativas de un mismo destino comparten trazado parcial (D010); R011/R013 con recorrido turístico por confirmar; HEN no mide dificultad técnica, exposición, estado del sendero ni aptitud personal.

## 5. Contraste con K-means (k = 2, 4 variables)

- Spearman entre HEN y el eje de centroides de K-means: 0,84; AUC (grupo de mayor ascenso frente al resto): 0,98.
- Las cuatro rutas del grupo K-means (R001, R003, R006, R022) ocupan las posiciones 1, 2, 3 y 5; **R020 (4.ª, 1,89 h) pertenece al grupo grande**. El mejor umbral de HEN (1,74 h) reproduce K-means con ARI 0,79, no 1,0. K-means en una dimensión sobre HEN da ARI 0,33.
- El orden continuo **no muestra un corte natural** entre las posiciones 4 y 5, donde K-means traza su frontera: la brecha R003→R020 es 0,35 h y R020→R022 0,15 h. La mayor brecha está entre R001 y R006 (0,89 h) y después entre R019 y R015 (0,42 h).
- Interpretación: K-means k = 2 separaba el ascenso alto; HEN integra además la distancia y por ello coloca a R020 (6,6 km) por encima de R022. Es la discrepancia de fondo señalada en el informe de validación (el 4/16 era un umbral de ascenso, no de tiempo).

## 6. Propuesta metodológica original

1. **Constructo:** el esfuerzo físico estimado se mide con HEN = d/5 + A/600 (distancia y ascenso), definido a priori.
2. **Altitud:** advertencia separada (valor en metros), nunca sumada al indicador ni a una clase.
3. **Presentación:** número en horas-equivalentes de referencia, posición entre las rutas analizadas y su rango de incertidumbre; etiqueta «estimación, no tiempo medido». **Sin categorías** mientras no exista una justificación independiente para cortes.
4. **Ascenso:** el del dataset (mediana de 3 puntos), con mediana-3 → crudo como **escenario de sensibilidad del DEM, no intervalo de confianza estadístico**.
5. **K-means/Ward/DBSCAN:** se conservan como contraste exploratorio, no como fuente de etiquetas.
6. **Antes de conectar a la página:** aprobar 1–4, definir cómo se redactan la incertidumbre y el aviso, y mantener 0 rutas habilitadas para recomendación hasta registrar la aprobación metodológica interna del protocolo. Orden previsto: lugar → destino exacto → alternativas reales → mapa, perfil y métricas → indicador de esfuerzo → advertencias separadas (altitud, acceso, estado).

Las tres decisiones de presentación de esta propuesta se resuelven para el siguiente prototipo en la sección 7; esto no aprueba una clasificación final.

## 7. Decisión técnica para el siguiente prototipo (sin aprobar clases)

Tras la reproducción local, se adopta **provisionalmente** V = 5 km/h y R = 600 m/h como convención comparativa de Naismith, no como predicción de duración en Pichincha. La página debe llamarlo «índice de esfuerzo de referencia (h-eq)», explicar la fórmula y evitar «tiempo estimado de llegada» o «duración prevista».

La comparación visible será **solo entre alternativas del mismo destino exacto**. Puede ordenarse por HEN, pero no mostrar un puesto global 1–20 al usuario ni insinuar que el valor menor es automáticamente la ruta «mejor» o más segura. Con una sola alternativa no hay puesto comparativo. La altitud, el acceso y el carácter técnico son avisos independientes.

El escenario mediana-3 → crudo debe estar disponible en un detalle desplegable «Sensibilidad del modelo de elevación», con la aclaración de que **no es un intervalo de confianza ni un rango de duración real**. La vista principal muestra el HEN base, distancia, ascenso y advertencias, sin categorías ni recomendaciones. Esta decisión autoriza preparar la visualización descriptiva, pero no abre la compuerta del modelo final.
