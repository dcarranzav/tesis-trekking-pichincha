# Clasificación de dificultad física estimada en tres niveles

**Fecha:** 23 de octubre de 2026. **Resultado:** 20 rutas clasificadas como Fácil, Moderada o Difícil mediante una regla explícita de cantidad de esfuerzo. La clasificación describe únicamente exigencia física estimada; no evalúa dificultad técnica, orientación, acceso, estado del sendero, clima, seguridad ni aptitud personal.

## Decisión metodológica

El plan de titulación propuso inicialmente las categorías Fácil, Moderada y Difícil y exigió reglas interpretables. No se fuerza un K-means con `k=3`: el análisis exploratorio mostró que esa partición no ofrece una mejora suficiente y produce grupos pequeños o sensibles. K-means se conserva como contraste de estructura de la muestra, no como fuente de los tres nombres.

La clasificación principal adapta la dimensión **cantidad de esfuerzo** del método MIDE. El manual oficial de MIDE calcula, para cada recorrido, un horario por distancia horizontal y otro por desnivel; toma el mayor y añade la mitad del menor. Sus velocidades de referencia son 400 m/h en subida, 600 m/h en bajada y entre 3 y 5 km/h según el piso. También divide la cantidad de esfuerzo en hasta 1 h, más de 1 a 3 h, más de 3 a 6 h, más de 6 a 10 h y más de 10 h. Fuente: https://montanasegura.com/MIDE/manualMIDE.pdf

Este proyecto dispone de geometría y elevación, pero no de una valoración homogénea del firme de las 20 rutas. Por eso utiliza 4 km/h como supuesto central de senda/camino y prueba 3 y 5 km/h como sensibilidad. No se afirma aplicar el MIDE completo.

## Regla reproducible

Para cada recorrido completo:

- `H_horizontal = distancia_total_km / 4 km/h`.
- `H_desnivel = desnivel_positivo_total_m / 400 m/h + desnivel_negativo_total_m / 600 m/h`.
- `H_estimada = max(H_horizontal, H_desnivel) + 0,5 × min(H_horizontal, H_desnivel)`.

En rutas de ida y vuelta, los desniveles del regreso se calculan invirtiendo el perfil de ida. En circuitos se utilizan directamente los ascensos y descensos del perfil completo. Las elevaciones provienen del perfil Copernicus DEM GLO-30 filtrado con mediana centrada de tres puntos.

Los cinco niveles de cantidad de esfuerzo de MIDE se adaptan a las tres categorías solicitadas por el plan:

| Categoría | Regla | Correspondencia utilizada |
|---|---:|---|
| **Fácil** | hasta 1 h estimada | MIDE esfuerzo 1 |
| **Moderada** | más de 1 y hasta 3 h estimadas | MIDE esfuerzo 2 |
| **Difícil** | más de 3 h estimadas | MIDE esfuerzo 3–5 agrupados |

Los términos son categorías de **dificultad física estimada**. Una ruta Fácil puede tener altitud, exposición, acceso restringido o problemas técnicos; esos aspectos deben mostrarse como avisos separados.

## Resultado de las 20 rutas

| Nivel | Rutas | Rango de horas estimadas | Rango de distancia |
|---|---:|---:|---:|
| Fácil | 8 | 0,17–0,90 h | 0,52–2,55 km |
| Moderada | 10 | 1,01–2,81 h | 1,66–7,48 km |
| Difícil | 2 | 4,06–4,64 h | 5,23–9,61 km |

Las rutas Difíciles son Sendero Cumbre Rucu Pichincha y Sendero al Ilaló. La tabla completa está en `07_resultados/tablas/clasificacion_dificultad_fisica_2026-10-23.csv`.

## Sensibilidad y límites

Se repitió la asignación con 3 y 5 km/h y con perfiles de elevación filtrados con mediana de cinco puntos o sin filtrar. Seis rutas cambian en al menos un escenario: R003, R004, R008, R019, R025 y R026. Deben mostrar un aviso de categoría sensible; no se oculta esa incertidumbre.

La sensibilidad al perfil crudo no significa que ese perfil sea preferible: el DEM de 30 m acumula ruido si no se filtra. La velocidad de 3–5 km/h representa supuestos sobre el piso, no mediciones de campo. La clasificación debe contrastarse posteriormente con dos o tres expertos, como prevé el plan, y la comprensión de las etiquetas debe evaluarse con usuarios. Hasta completar esas actividades, las categorías son el resultado técnico reproducible del proyecto, pero no una certificación externa.

## Relación con K-means y la interfaz

- La regla MIDE adaptada es la clasificación principal Fácil/Moderada/Difícil.
- K-means k=2 queda como análisis exploratorio de la estructura relativa de distancia y ascenso; no debe aparecer como una segunda clasificación pública.
- El antiguo indicador HEN queda como antecedente/contraste y no debe competir con la categoría principal en las tarjetas.
- La clasificación no habilita recomendaciones de salida. Comparar alternativas del mismo destino sigue siendo una función secundaria del dashboard.

## Reproducción

```powershell
python 06_scripts/clasificar_dificultad_fisica.py --fecha 2026-10-23
```

Salidas:

- `clasificacion_dificultad_fisica_2026-10-23.csv`
- `clasificacion_dificultad_fisica_resumen_2026-10-23.csv`
- `clasificacion_dificultad_fisica_sensibilidad_2026-10-23.csv`
- `clasificacion_dificultad_fisica_parametros_2026-10-23.json`

El JSON conserva fórmula, parámetros, versión, fuentes y huellas SHA-256 del dataset y de la clasificación.
