# Experimento K-means k=3 para la dificultad física estimada

**Fecha:** 10 de noviembre de 2026. **Estado:** contraste exploratorio; no cambia la clasificación pública (regla de esfuerzo adaptada de MIDE: 8 Fácil, 10 Moderada, 2 Difícil). **Diseño y criterios de aceptación:** `diseno_experimento_kmeans_k3_2026-11-10.md`, escrito antes de ejecutar. **Script:** `06_scripts/evaluar_kmeans_k3_dificultad.py`. **Salidas:** `07_resultados/tablas/kmeans_k3_*_2026-11-10.{csv,json}`.

## 1. Decisión

**Opción B, según los criterios fijados para este experimento.** Es la decisión automática de las reglas C1–C5, que no se modificaron después de ver los resultados. La conclusión científica, más matizada, está en la sección 12: el uso de k=3 **no está justificado todavía** para sustituir la clasificación pública; no es una refutación definitiva. Se conserva la regla física como clasificación pública. Las reglas fijadas a priori produjeron B porque fallan dos criterios: C3 (el grupo más pequeño tiene 2 rutas; el mínimo era 3) y C5 (con el ascenso calculado sobre el perfil DEM crudo, una prueba de estrés con ruido documentado, cambian 4 rutas, ARI 0,5606; el mínimo era 0,80. Con la mediana de 5 puntos, la alternativa de procesamiento más comparable, la partición se conserva: ARI 1,000). Los criterios C1, C2 y C4 sí se cumplieron.

K-means no genera las tres categorías públicas: aporta una descripción de la estructura de las 20 rutas (qué rutas se parecen en distancia y ascenso) y muestra una coincidencia parcial con la regla en el extremo alto. Como ambos métodos utilizan medidas relacionadas, esa coincidencia no valida la regla de forma independiente. K-means no reproduce el umbral de 1 hora y su grupo superior, de dos rutas, es frágil.

## 2. Muestra y variables

- Se comprobó el conteo actual: **27 rutas procesadas, 20 elegibles y 7 no elegibles** (R002, R005, R007, R009, R010, R012 y R014). Las 20 coinciden exactamente con las de `clasificacion_dificultad_fisica_2026-10-23.csv`. Sin datos faltantes.
- Variables: distancia total y ascenso total, z-score (ddof=0), pesos 1:1, distancia euclídea. KMeans k-means++, `n_init=10`, semillas 0–49, mínima inercia (desempate por semilla). Python 3.13.16, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, scikit-learn 1.9.1.
- **Dependencia entre variables:** Pearson 0,829 y Spearman 0,926 entre distancia y ascenso. Los grupos se alinean sobre un eje dominante de «tamaño del recorrido». Además, las 20 rutas no son independientes: 13 identificadores de destino y 16 destinos exactos; Yellow House (R017, R020, R021), el extremo común de Yanacocha (R011, R013) y el Mirador Cerro de la Luz (R024, R025) agrupan alternativas relacionadas, y R006 y R022 son del mismo cerro. La silueta y la estabilidad pueden sobrestimar la separación real.

## 3. K-means con k=2, 3 y 4 (mismas 20 rutas)

| k | Tamaños | Inercia | Silueta | ARI mín. entre 50 semillas | Semillas con la misma partición | ARI con Ward |
|---:|---|---:|---:|---:|---:|---:|
| 2 | 12 / 8 | 12,9118 | 0,5919 | 1,000 | 50/50 | 1,000 |
| 3 | 12 / 6 / 2 | 6,1769 | 0,5895 | 1,000 | 50/50 | 0,9246 |
| 4 | 7 / 6 / 5 / 2 | 4,5064 | 0,4354 | 0,5111 | 47/50 (3 semillas dan 12/5/2/1) | 0,5111 |

Las cifras de k=2 y k=3 reproducen las del 22 de octubre. El ensayo anterior de cuatro variables (silueta 0,3203, ARI mínimo 0,462) no se repitió aquí.

## 4. Los tres grupos de k=3

Orden físico: suma de las coordenadas estandarizadas del centroide (solo las variables del modelo). Los índices 0/1/2 de K-means no significan Fácil/Moderada/Difícil.

| Grupo | n | Rutas | Distancia, km: rango (mediana) | Ascenso, m: rango (mediana) | Esfuerzo estimado, h: rango (mediana) |
|---|---:|---|---|---|---|
| G1 menor | 12 | R004, R008, R011, R013, R015, R016, R018, R023, R024, R025, R026, R027 | 0,52–3,34 (1,60) | 20–239 (128) | 0,17–1,39 (0,76) |
| G2 intermedio | 6 | R003, R017, R019, R020, R021, R022 | 4,36–7,48 (5,64) | 280–521 (326) | 1,89–2,81 (2,21) |
| G3 mayor | 2 | **R001, R006** | 5,23–9,61 (7,42) | 818–825 (821) | 4,06–4,64 (4,35) |

Se verificó que el grupo de dos rutas es **R001 y R006**.

- **Inversiones:** ninguna. Ninguna ruta de un grupo inferior exige más esfuerzo estimado que una de un grupo superior.
- **Solapamientos:** sin solapamiento en ascenso ni en esfuerzo estimado entre grupos adyacentes. Sí hay solapamiento en **distancia** entre G2 y G3: R003 (7,48 km, G2) es más larga que R006 (5,23 km, G3). El grupo G3 queda definido por el ascenso, no por la distancia.
- Los límites entre grupos son huecos de los datos, no umbrales de esfuerzo: entre G1 y G2 hay un vacío de 1,39 a 1,89 h y entre G2 y G3 de 2,81 a 4,06 h. Si se retira o se añade una ruta, el hueco se mueve.

### Rutas fronterizas (umbrales fijados antes: silueta individual < 0,35 o margen relativo < 0,25)
Quedan marcadas **R001** (silueta 0,318), **R006** (0,139), **R015** (0,315) y **R023** (0,345). R015 y R023 están entre G1 y G2 (margen relativo 0,54 y 0,64). R006 es la ruta peor asignada del conjunto.

Casos pedidos: R003 (silueta 0,435; margen 1,06), R017 (0,604), R019 (0,469), R020 (0,677) y R021 (0,649) pertenecen claramente a G2. **R022** (0,401; margen 1,05) pertenece a G2 en K-means, pero **Ward con k=3 la coloca en el grupo superior** con R001 y R006, y con la pendiente media como tercera variable pasa a G3.

## 5. Robustez

| Escenario | Resultado | ARI con la base | Rutas que cambian |
|---|---|---:|---|
| Semillas (50) | misma partición en 50/50 | 1,000 | — |
| Pesos moderados (distancia o ascenso ×0,8 o ×1,25) | 12/6/2 | 1,000 | ninguna |
| Pesos de estrés (×0,5 o ×2) | dos escenarios dan 12/7/1 | 0,9255 en dos escenarios | R006 abandona G3 y queda G3 con solo R001 |
| Ascenso con mediana de 5 puntos | 12/6/2 | 1,000 | ninguna |
| **Ascenso con perfil DEM crudo** | 10/6/4, silueta 0,4949 | **0,5606** | R003, R015, R019, R023 |
| Con pendiente media absoluta | 12/5/3, silueta 0,4345 | 0,9246 | R022 |
| Con elevación máxima (contexto, no esfuerzo) | 8/8/4, silueta 0,4435 | **0,3369** | 14 rutas |
| Retirar una ruta (20 escenarios) | 19 escenarios dan ARI 1,000 | 0,9295 sin R001 | sin R001: R022; **sin R006: G3 queda con una ruta (12/6/1)** |
| Retirar R026 y R027 | 10/6/2 | 1,000 | ninguna |
| Una alternativa por destino (4 variantes) | 8/3/2, 7/4/2, 10/4/2 y 10/4/2 | 1,000 | ninguna, pero ver abajo |
| Ward con k=3 | ARI con K-means 0,9246 | — | R022 |

Debilidades que no se esconden:
- Con una alternativa por destino, la mejor partición coincide con la base, pero en las dos variantes «corta» la estabilidad entre semillas baja (ARI mínimo 0,895 y 0,530): el ajuste depende más de la inicialización cuando hay menos rutas.
- El grupo superior depende de dos rutas. Si desaparece una, el grupo se vuelve una ruta o cambia de composición.
- El resultado depende de la elección de variables: al añadir elevación máxima la partición cambia en 14 de 20 rutas. Esta variable es contexto de exposición y no trabajo acumulado, por eso no se usa, pero muestra que K-means no es neutral frente a las variables.
- No hubo fallos de ejecución en ningún escenario.

### DBSCAN sobre las mismas dos variables
Con `eps` 0,5–0,6 y `min_samples` 2–4 forma dos grupos y marca como ruido 3 o 4 rutas (R001, R006, R022 y, con `eps` 0,5, también R003); cobertura 0,80–0,85. El ARI con K-means k=3 **solo sobre las rutas no ruido** es 1,000, pero no es acuerdo sobre las 20: tratando el ruido como un grupo, el ARI baja a 0,87–0,92. DBSCAN solo forma tres grupos con `eps` 0,3 o 0,4 y `min_samples` 2, con 4 a 6 rutas como ruido (cobertura 0,70–0,80) y ARI 0,55–0,68; con `eps` ≥ 0,75 forma un solo grupo. No respalda tres grupos estables sobre las 20 rutas.

## 6. Comparación con la regla vigente (no es verdad de terreno)

| Grupo K-means k=3 | Fácil | Moderada | Difícil |
|---|---:|---:|---:|
| G1 menor | 8 | 4 | 0 |
| G2 intermedio | 0 | 6 | 0 |
| G3 mayor | 0 | 0 | 2 |

16 de las 20 rutas coinciden por orden y 4 discrepan. ARI = 0,392 y correlación de rangos entre grupo y esfuerzo estimado = 0,871; son descripciones de concordancia, no una medida de exactitud.

| Ruta | Distancia, km | Ascenso, m | Esfuerzo, h | Regla | K-means k=3 |
|---|---:|---:|---:|---|---|
| R004 | 1,663 | 192,8 | 1,011 | Moderada | G1 |
| R026 | 2,133 | 180,0 | 1,017 | Moderada | G1 |
| R023 | 3,339 | 203,4 | 1,265 | Moderada | G1 |
| R015 | 3,155 | 239,3 | 1,391 | Moderada | G1 |

Las cuatro discrepancias están en el límite inferior: la regla las coloca por encima de 1 hora y K-means las deja en el grupo de menor esfuerzo. R004 y R026 están a menos de 0,02 h del umbral.

**Qué aporta cada método.** La regla: umbrales con unidad (horas de marcha efectiva), significado para quien camina, independencia de la muestra (una ruta nueva se clasifica sin tocar las demás), estabilidad (6 rutas cambian de nivel en algún escenario de sensibilidad, y esto se informa ruta por ruta) y una explicación comprensible. Pierde que sus umbrales provienen de una adaptación de MIDE y no de los datos. K-means k=3: describe la estructura real de las 20 rutas sin imponer umbrales y confirma que las dos rutas más exigentes forman un grupo separado. Pierde interpretabilidad (los límites son huecos de la muestra, no horas ni metros), estabilidad (el grupo superior depende de dos rutas; con el ascenso DEM crudo, prueba de estrés, cambian 4 asignaciones) y capacidad de comunicación: «G3» o «grupo intermedio» no dicen cuánto esfuerzo implican y los grupos cambiarían si la muestra cambia.

## 7. Justificación de la decisión B según los criterios

- El grupo de dos rutas es una debilidad importante para una categoría pública: sus dos rutas determinan el centroide y una de ellas (R006) es la peor asignada (silueta 0,139); sin R006 el grupo queda con una ruta y con pesos de estrés R006 sale del grupo. Esto no prueba por sí mismo que sea imposible describir ese grupo, pero una categoría apoyada en una o dos observaciones tiene poca estabilidad.
- G1 mezcla 8 rutas Fácil y 4 Moderada de la regla: llamarlo «Fácil» etiquetaría como fáciles rutas de 1,0 a 1,4 horas de marcha estimada. Como la regla no es verdad de terreno, esto es una diferencia de criterio y no un error medible.
- La coherencia física de K-means es real (sin inversiones, silueta 0,59, semillas estables, estable a pesos moderados y a retirar una ruta), pero la evidencia es de una muestra intencional de 20 rutas con observaciones relacionadas. Ward, DBSCAN y la silueta son evidencia interna sobre estas rutas y **no** una validación externa de la dificultad percibida por personas.
- No se propone A, por lo que no se define una asignación pública de rutas nuevas. El script guarda escalador y centroides (`asignar_nueva_ruta`), solo para reproducir las asignaciones y marcar extrapolación fuera del rango de entrenamiento (distancia 0,515–9,607 km; ascenso 19,7–824,8 m).

## 8. Función de K-means en la tesis

K-means forma tres grupos en este ensayo, pero no genera las tres categorías públicas Fácil, Moderada y Difícil. Se usó para explorar si la estructura de las 20 rutas en distancia y ascenso sugiere grupos naturales. Con k=2 y k=3 aparece una separación estable entre un grupo numeroso de rutas cortas y de poco ascenso y rutas más largas y exigentes; con k=3 las dos rutas de mayor ascenso (R001 y R006) forman un grupo propio. Esto es consistente con que la regla marque a ambas como Difícil, pero no sustituye a la regla ni la valida externamente.

## 9. Qué validación adicional resolvería la cuestión
- Etiquetas externas (panel de especialistas o guías, o esfuerzo percibido por caminantes) para contrastar tanto la regla como los grupos.
- Más rutas, sobre todo de esfuerzo alto, para que el grupo superior no dependa de dos observaciones.
- Un análisis con los perfiles DEM de mayor resolución o validados en campo, porque el ascenso crudo cambia cuatro asignaciones.

## 10. Limitaciones
- Los criterios de aceptación se fijaron antes de ejecutar este experimento, pero después de ensayos previos sobre los mismos datos (22 de octubre); no son una preregistro en sentido estricto.
- Muestra intencional de 20 rutas, 13 destinos, alternativas solapadas y DEM de 30 m. Las rutas con trazado público de OpenStreetMap no son una muestra representativa.
- El experimento se ejecutó en un contenedor Linux (Python 3.13.16, scikit-learn 1.9.1). ChatGPT lo reprodujo de forma independiente en el entorno Windows del proyecto (12 pruebas y un cálculo propio de K-means) y confirmó 12/6/2, silueta 0,5895 y las cuatro discrepancias.
- Esfuerzo estimado, silueta y ARI describen estas rutas; no miden seguridad, dificultad técnica, acceso, clima ni aptitud personal.

## 11. Reproducción

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$env:OMP_NUM_THREADS = '1'
& 'C:\Users\LENOVO\miniforge3\envs\trekking_pichincha\python.exe' 06_scripts\evaluar_kmeans_k3_dificultad.py --fecha 2026-11-10
& 'C:\Users\LENOVO\miniforge3\envs\trekking_pichincha\python.exe' -m unittest tests.test_evaluar_kmeans_k3_dificultad tests.test_evaluar_kmeans_esfuerzo -v
```

Archivos: `kmeans_k3_{metricas,semillas,asignaciones,centroides,grupos_descripcion,solapamientos,inversiones,sensibilidad,dbscan,comparacion_regla_matriz,comparacion_regla_discrepancias,criterios}_2026-11-10.csv` y `kmeans_k3_parametros_2026-11-10.json`.

## 12. Interpretación: qué está confirmado y qué falta

Esta sección separa la decisión automática (B, registrada tal como salió) de la conclusión científica. No modifica resultados, asignaciones vigentes ni los criterios C1–C5.

**Resultados confirmados** (también por la reproducción independiente en Windows)
- K-means con k=3 sobre distancia y ascenso forma 12/6/2 con silueta 0,5895 y es idéntico en las 50 semillas; los grupos están ordenados sin inversiones de esfuerzo entre grupos adyacentes.
- El grupo superior es R001 y R006; el grupo menor incluye las cuatro rutas R004, R015, R023 y R026 que la regla clasifica como Moderada.
- La partición se conserva con pesos moderados, con la mediana de 5 puntos, al retirar una ruta cualquiera (salvo cambios menores: sin R001 pasa R022), al retirar R026 y R027 y con una alternativa por destino.

**Debilidades reales**
- Un grupo de dos rutas (R001 y R006) determina el extremo alto; R006 es la ruta peor asignada. Si se retira R006, el grupo queda con R001 sola; con pesos de estrés, R006 cambia de grupo.
- Las dos variables están muy correlacionadas (Pearson 0,829; Spearman 0,926) y las 20 rutas incluyen alternativas relacionadas, de modo que la separación aparente puede sobrestimarse.
- Los límites entre grupos son huecos de los datos (1,39 a 1,89 h y 2,81 a 4,06 h), no umbrales con significado de esfuerzo.
- La partición depende de las variables: al añadir elevación máxima, que no es esfuerzo acumulado, cambia en 14 de las 20 rutas.

**Límites de los criterios de aceptación** (no se alteran, pero conviene interpretarlos así)
- C3 (mínimo de 3 rutas por grupo) y C5 fueron fijados por el experimentador antes de ejecutar, pero después de ensayos previos sobre los mismos datos; no son un preregistro estricto.
- C5b combina dos escenarios que no son equivalentes: el ascenso DEM crudo es una prueba de estrés con ruido documentado, mientras que la mediana de 5 puntos es la alternativa de procesamiento más comparable y conserva la partición (ARI 1,000). El criterio falla por el escenario de estrés, no por el procesamiento comparable.
- La regla de decisión «dos criterios fallidos implican B» es una convención; con otro peso de cada criterio la lectura podría ser C. B se mantiene registrada.
- Las cuatro discrepancias con la regla no miden exactitud: la regla MIDE adaptada no es verdad de terreno. ARI 0,392 y 16 coincidencias son descripciones de concordancia.

**Evidencia que falta para llamar Fácil/Moderada/Difícil a los grupos**
- Etiquetas o juicios externos independientes (especialistas, guías o esfuerzo percibido por caminantes) que permitan contrastar los grupos y la regla.
- Más rutas, sobre todo de esfuerzo alto, para que el extremo superior no dependa de dos observaciones, y menos alternativas solapadas.
- Una definición de límites con significado de esfuerzo (por ejemplo, horas de marcha efectiva o desniveles), no solo huecos de la muestra.
- Perfiles DEM verificados o de mayor resolución para saber si el ruido del ascenso crudo es realmente un problema o una prueba de estrés extrema.

**Conclusión.** Con la evidencia actual, el uso de K-means k=3 **no está justificado todavía** para sustituir la clasificación pública de tres niveles. No se concluye que sea imposible: los resultados son internamente coherentes, pero insuficientes para dar nombres de dificultad a los grupos. La clasificación pública se mantiene y K-means sigue siendo un contraste exploratorio.
