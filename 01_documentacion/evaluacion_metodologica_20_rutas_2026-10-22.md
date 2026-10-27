# Evaluación metodológica inicial con 20 rutas elegibles

**Fecha:** 2026-10-22. **Estado:** evaluación iniciada, **sin modelo final, niveles de esfuerzo ni recomendaciones publicados**.

## Muestra y puerta de calidad

El dataset contiene 27 rutas procesadas, 20 elegibles provisionales y 7 no elegibles. Las cinco variables candidatas no tienen valores faltantes. La auditoría integral registra 263/263 controles OK y la suite 117 pruebas correctas. El control espacial marca un duplicado potencial entre R005 (no elegible) y R026; R027 no tiene alerta de duplicidad. R011/R013 siguen con recorrido turístico completo por confirmar y varias rutas tienen advertencias de acceso, lo que obliga a separar elegibilidad para el análisis de recomendación pública.

## Evidencia estadística exploratoria

Los resultados reproducibles están en `ensayo_clustering_exploratorio_sklearn_2026-10-22_r027.md` y los CSV asociados. Se estandarizaron las variables en cada escenario; se probaron K-means para k=2–4 con 30 semillas, grupos no unitarios y Ward como contraste.

| Escenario | k | Silueta | Tamaños | ARI Ward | ARI mínimo entre semillas |
|---|---:|---:|---:|---:|---:|
| 4 variables base | 2 | 0,448 | 4/16 | 1,000 | 1,000 |
| 4 variables base | 3 | 0,320 | 3–11 | 0,747 | 0,462 |
| 4 variables base | 4 | 0,335 | 2–8 | 0,447 | 0,335 |
| 5 variables, con pendiente p95 | 2 | 0,378 | 5/15 | 0,785 | 1,000 |

En este corte, **k=2 es el candidato estadístico más estable**, no una decisión final ni una escala automática «fácil/difícil». El grupo de 4 rutas contiene R001, R003, R006 y R022; el de 16 contiene las demás, incluida R027. Debe verificarse si la diferencia representa esfuerzo físico interpretable y no predominantemente altitud o composición de destinos. Los números 0 y 1 son arbitrarios.

La correlación máxima de Spearman entre variables candidatas es 0,926, por lo que la redundancia entre distancia y ascenso exige una elección justificada. Retirar distancia aumenta la silueta de k=2 a 0,516, pero cambia asignaciones respecto de la base (ARI 0,764); retirar ascenso da ARI 1,000 frente a la base, aunque cambia la estabilidad entre semillas. Esto **no autoriza** escoger variables por la silueta más alta aislada.

Retirar R027 deja iguales las asignaciones comunes para k=2 (ARI 1,000); para k=3 el ARI baja a 0,815 y para k=4 a 0,514. Retirar R026 tampoco cambia las asignaciones comunes de k=2, pero k=4 baja a ARI 0,649. La aparente robustez de k=2 no elimina las dudas de acceso, trazado o interpretación.

DBSCAN se ejecutó solo como contraste, no como generador de etiquetas. Con `min_samples=2` y `eps=1,0` deja 5 de 20 rutas como ruido; con `min_samples=3` y el mismo `eps` deja 7. Sus resultados dependen fuertemente de parámetros y no sustituyen la decisión interpretativa sobre K-means.

## Antes de publicar clases

1. Revisar la pertinencia y redundancia de variables, el peso implícito de la altitud y la estabilidad de centroides y membresías al variar k, semillas y rutas con incertidumbre.
2. Examinar perfiles de los grupos y definir nombres de esfuerzo solo si sus gradientes son coherentes; no reutilizar dificultades descriptivas de portales como etiquetas verdaderas.
3. Mantener por separado advertencias de alta montaña, estado del sendero, acceso y seguridad. La clase física nunca certificará aptitud personal o tránsito seguro.
4. Documentar versión de datos, parámetros, interpretación y pruebas de sensibilidad. Registrar una aprobación metodológica interna conforme al protocolo del proyecto; no se requiere autorización del tutor como criterio de elegibilidad de ruta.
5. Solo después generar el archivo de niveles y su registro de validación con hash. Hasta entonces, `estado_clasificacion` debe mantener 0 rutas habilitadas para recomendación.

R027 cumple la meta numérica mínima, pero la investigación no termina al alcanzar 20: se conserva el trabajo de verificación pendiente y la clasificación final permanece bloqueada.
