# Informe de validación metodológica de la agrupación exploratoria (20 rutas)

> **Nota de vigencia (23 de octubre de 2026):** este informe documenta el corte y las comparaciones previas. La salida categórica principal posterior es Fácil/Moderada/Difícil mediante la regla descrita en `clasificacion_dificultad_fisica_tres_niveles_2026-10-23.md`. Las conclusiones sobre K-means se conservan como contraste histórico.

**Fecha:** 2026-10-22. **Estado:** validación interna ejecutada; **decisión: no se publican niveles de esfuerzo ni recomendaciones**. No se creó `niveles_esfuerzo_finales.csv` ni `validacion_modelo_final.json`; la compuerta sigue en 0 rutas habilitadas. Repetida en el entorno local del proyecto el 2026-10-22: script correcto, notebook 05 ejecutado, 122 pruebas OK y auditoría 266/266 (0 advertencias, 0 errores).

Reproducir: `python 06_scripts/validar_metodologia_clasificacion.py --fecha 2026-10-22` (salidas `07_resultados/tablas/validacion_*_2026-10-22.csv|json`, figuras `07_resultados/figuras/validacion_*_2026-10-22.png`). Entorno de esta ejecución: Python 3.13, scikit-learn 1.9.1, pandas 3.0.5 (ejecución en el espacio de trabajo remoto, no en el entorno `trekking_pichincha`; ver «Límites»).

## 1. Muestra, variables y reproducción

- Dataset `dataset_clasificacion_rutas.csv`: 27 rutas, 20 `elegible_actual` y 7 `no_elegible_aun`. Las 20 elegibles tienen ID únicos, 0 valores faltantes, 13 destinos distintos (D010 tiene 5 alternativas; D004, D009 y D014 tienen 2).
- Variables (sin cambios): `distancia_total_km`, `ascenso_total_m`, `elevacion_max_m`, `pendiente_media_abs_pct`; `pendiente_p95_abs_pct` solo como sensibilidad. `StandardScaler` (media 0 con error máximo 3,4·10⁻¹⁶; desviación 1,0), K-means con `n_init=10` y 50 semillas (0–49), Ward con distancia euclídea, DBSCAN `eps` ∈ {0,5; 0,75; 1; 1,25; 1,5; 2} × `min_samples` ∈ {2, 3, 4}.
- **Reproducción independiente** de `evaluacion_clustering_exploratorio_sklearn_2026-10-22_r027.csv` (escenario base): silueta, inercia y asignaciones (ARI 1,0) coinciden para k = 2, 3 y 4. Las cifras del informe previo se confirman.

## 2. K-means k = 2, 3, 4 (base de 4 variables)

| k | Silueta | Inercia | Tamaños | ARI mín. entre semillas | Semillas que dan la mejor partición | ARI Ward |
|---:|---:|---:|---|---:|---:|---:|
| 2 | 0,448 | 44,10 | 4/16 | 1,000 | 50/50 | 1,000 |
| 3 | 0,320 | 30,86 | 3/6/11 | 0,462 | 44/50 | 0,747 |
| 4 | 0,335 | 23,12 | 2/2/8/8 | 0,335 | 33/50 | 0,447 |

k = 3 y k = 4 no son estables (ni entre semillas ni frente a Ward) y k = 4 tiene grupos de 2 rutas. Retirar una ruta cambia k = 3 hasta ARI 0,43 (R025) y 0,46 (R017, R019, R020, R021). **Se descartan.** k = 2 es estable en semillas, Ward y al retirar cualquier ruta (ARI mínimo 1,0).

### Centroides en unidades originales (k = 2)

| Grupo | n | Distancia total, km (media; rango) | Ascenso, m | Altitud máx., m | Pendiente media, % |
|---|---:|---|---|---|---|
| Menor ascenso | 16 | 2,73 (0,52–6,63) | 167 (20–339) | 2 193 (1 284–3 549) | 12,7 (5,4–23,2) |
| Mayor ascenso | 4 (R001, R003, R006, R022) | 6,67 (4,36–9,61) | 653 (449–825) | 3 558 (3 082–4 679) | 21,1 (12,0–31,3) |

## 3. ¿Qué separa realmente el grupo 4/16?

- **Es el ascenso acumulado.** K-means con solo `ascenso_total_m` reproduce exactamente la partición (ARI 1,0) y el ascenso separa los grupos sin solapamiento: máximo del grupo grande 339 m (R020), mínimo del pequeño 449 m (R003). Con solo distancia el ARI es 0,33; con solo pendiente media, 0,37; con solo altitud, −0,01; con p95, 0,06.
- **No es la altitud:** la altitud máxima solapa (R011/R013 llegan a 3 549 m y están en el grupo grande). Retirar la altitud o reducir su peso a 0,5 deja la partición idéntica; **duplicar su peso la cambia por completo** (grupos 10/10, ARI 0,13): la altitud es un eje distinto que, sobrepesado, domina y separa zonas altas de bajas, no esfuerzo.
- **No coincide con un índice de tiempo a priori.** La regla de Naismith (h = km/5 + m/600, sin usar etiquetas turísticas) ordena R001 3,3 h, R006 2,4, R003 2,2, **R020 1,9 (grupo grande)**, R022 1,7 (grupo pequeño), R021/R017 1,6. K-means sobre ese índice coincide solo con ARI 0,33. Las rutas largas y de poco desnivel (R020, R017, R021) quedan en el grupo «menor ascenso» aunque tarden más que R022.
- **Rutas extremas:** R001 y R006 son las de mayor ascenso (825 y 818 m) y R001 la de mayor distancia y altitud; con todo, retirar cualquiera de las 20 rutas no cambia la partición k = 2 (ARI 1,0).
- Redundancia: Spearman distancia–ascenso 0,93 (pendiente media–p95 0,87). Retirar distancia da 3/17 (ARI 0,76 frente a la base: R003 pasa al grupo grande); retirar ascenso da el mismo 4/16 (ARI 1,0, pero estabilidad entre semillas 0,58): la distancia reproduce el ascenso por correlación.

## 4. DBSCAN como contraste (sin tratarlo como prueba)

Malla de 18 configuraciones (`validacion_dbscan_malla_2026-10-22.csv`). Con `eps` ≤ 1,25 el resultado oscila entre 0 y 3 grupos y entre 5 y 20 rutas ruido (cobertura 0–75 %); con `eps` 1,5 casi todo es un único grupo (4 ruido) y con 2,0 queda 1–2 ruido (R001; R001 y R006 con `min_samples` 4). La silueta sin ruido (hasta 0,84) no es comparable con la de K-means porque excluye entre 5 y 13 rutas en las configuraciones que forman ≥ 2 grupos.

- **Hallazgo comprobado:** en las **9 configuraciones que forman ≥ 2 grupos, R001, R003, R006 y R022 son ruido en las 9.** DBSCAN los trata como puntos aislados, no como un segundo grupo.
- Comparación con K-means k = 2 solo entre rutas no ruido: **no es informativa** porque todas las rutas retenidas pertenecen al mismo grupo de K-means (entre 5 y 13 quedan fuera por ruido); el script marca `comparable=False` y deja el ARI vacío. DBSCAN subdivide el grupo grande; **no confirma ni contradice** la separación 4/16, solo muestra que esas cuatro rutas son poco densas. Frente a k = 3 el ARI llega a 0,59 con 13 rutas fuera, sin valor concluyente.
- Con `eps` ≥ 1,5 el ARI no está definido (un único grupo) y no se reporta como acuerdo.
- Estabilidad de DBSCAN al retirar una ruta (ARI mínimo en rutas no ruido en ambas corridas): 0,76–0,77 con `min_samples` 2 y `eps` 1–1,25; 0,72 con `min_samples` 3 y `eps` 1; 1,0 en el resto de configuraciones con ≥ 2 grupos. Es un contraste de estabilidad, no de validez.

## 5. Sensibilidad (k = 2; k = 3 en `validacion_sensibilidad_2026-10-22.csv`)

| Escenario | n | Tamaños | ARI vs. base (rutas comunes) | Grupo mayor ascenso |
|---|---:|---|---:|---|
| sin R026 | 19 | 4/15 | 1,00 | R001, R003, R006, R022 |
| sin R027 | 19 | 4/15 | 1,00 | igual |
| sin R026 ni R027 | 18 | 4/14 | 1,00 | igual |
| sin R011/R013 (por confirmar) | 18 | 4/14 | 1,00 | igual |
| sin rutas muy solapadas (R016, R020, R021) | 17 | 4/13 | 1,00 | igual |
| una alternativa por destino (más larga / más corta) | 13 | 4/9 | 1,00 / 1,00 | igual |
| sin distancia | 20 | 3/17 | 0,76 | R001, R006, R022 |
| sin ascenso | 20 | 4/16 | 1,00 | igual (semillas 0,58) |
| sin altitud / altitud ×0,5 | 20 | 4/16 | 1,00 | igual |
| **altitud ×2** | 20 | 10/10 | **0,13** | cambia por completo |
| con pendiente p95 | 20 | 5/15 | 0,79 | + R004 |

R026 se solapa con R005 (R005 no es elegible); su retirada no altera la partición. **Permanece:** k = 2 como «cuatro rutas de mayor ascenso» frente al resto. **Cambia:** k = 3 (ARI frente a la base entre 0,41 y 0,82 en la mayoría de escenarios; 0,51–0,69 con una alternativa por destino) y k = 4; y k = 2 bajo sobreponderación de la altitud. No se eligió ninguna variante por su silueta (la más alta, 0,52 sin distancia, no se adopta).

## 6. Criterios explícitos de esta evaluación

Estos umbrales quedaron codificados antes de ejecutar este script, pero **no son una preregistración independiente**: ya existían ensayos exploratorios sobre las mismas rutas. Por ello, el cumplimiento de 6/7 sirve como diagnóstico interno y no como confirmación externa del modelo.

| Criterio | Valor | Umbral | ¿Cumple? |
|---|---:|---|:--:|
| C1 ARI mín. entre semillas | 1,00 | ≥ 0,90 | sí |
| C2 ARI con Ward | 1,00 | ≥ 0,90 | sí |
| C3 ARI mín. al retirar una ruta | 1,00 | ≥ 0,70 | sí |
| C4 Tamaño mínimo de grupo | 4 | ≥ 3 | sí |
| C5 Silueta k = 2 | 0,448 | ≥ 0,40 | sí |
| C6 Sensibilidad a rutas, pesos y destinos (ARI mín.) | 0,13 | ≥ 0,70 | **no** (altitud ×2) |
| C7 Sensibilidad a cambio de variables (ARI mín.) | 0,76 | ≥ 0,70 | sí |

## 7. Decisión

1. **No hay base para tres o más niveles.** k = 3 y k = 4 son inestables.
2. **Dos grupos son estadísticamente defendibles pero su interpretación es limitada.** Con 6 de 7 criterios cumplidos (el C6 falla solo por el escenario de altitud ×2), la partición es robusta a semillas, método (Ward), retiro de rutas y solapamientos. Pero equivale a un umbral de ascenso acumulado (entre 339 y 449 m); ni DBSCAN ni un índice de tiempo a priori la reproducen, y el grupo «menor ascenso» es heterogéneo (0,5–6,6 km; 20–339 m). El único nombre defendible es descriptivo: **«ascenso acumulado alto (≥ ~450 m)» frente a «menor ascenso acumulado»**; no «difícil» o «fácil», ni una certificación de seguridad, acceso o aptitud personal. Los números 0/1 no son clases.
3. **La clasificación de esfuerzo sigue exploratoria.** Correcciones metodológicas necesarias antes de publicar clases: (a) definir a priori el constructo (tiempo y desnivel, por ejemplo con una regla de tiempo de marcha documentada) y justificar variables en lugar de depender solo del agrupamiento sin etiquetas; (b) tratar la altitud como contexto/advertencia, no como variable de esfuerzo en la agrupación (coherente con la separación ya adoptada entre clase física y advertencias de altura); (c) valorar un índice continuo con ranking en lugar de clases con 4 rutas en un grupo; (d) ampliar la muestra, hoy 13 destinos (4 rutas en un grupo, 5 alternativas de un mismo destino). No se entrena Random Forest: no hay etiquetas válidas.
4. Esta decisión es interna y exploratoria. No sustituye la aprobación metodológica interna del protocolo, que no se registra.

## 8. Integración prevista en esta corrida (estado histórico)

Esta sección documenta la decisión del ensayo anterior de cuatro variables. Fue superada, el mismo 22 de octubre, por el modelo físico vigente de distancia total y ascenso acumulado descrito en `informe_modelo_kmeans_fisico_2026-10-22.md`. La página ahora muestra sus dos clases relativas y los cuatro casos sensibles, manteniendo 0 rutas habilitadas para recomendación. El orden sigue siendo lugar → destino exacto → alternativas reales de ese destino → mapa, perfil y métricas → clase física y advertencias por separado; no se mezclan destinos ni se crean alternativas.

## 9. Límites

- n = 20 rutas, 13 destinos; las alternativas de un mismo destino no son independientes (R020/R021/R017 comparten trazado parcial, D010).
- No hay etiquetas de esfuerzo validadas: la validación es interna (estabilidad), no externa (exactitud).
- `ascenso_total_m` y pendientes provienen de un DEM de 30 m y sufren error de suavizado; las pendientes p95 son más sensibles.
- Esta corrida se hizo con scikit-learn 1.9.1 en el espacio de trabajo remoto; debe repetirse en el entorno del proyecto con el comando anterior (las tablas deberían coincidir).
