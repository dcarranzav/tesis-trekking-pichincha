# Decisión de interfaz: grupos de esfuerzo relativo con K-means k=3

**Fecha:** 10 de noviembre de 2026. **Ámbito:** página de demostración de la tesis; 20 rutas elegibles de 27 procesadas.

## Qué muestra la página

La categoría visible de cada ruta procede de `kmeans_k3_asignaciones_2026-11-10.csv`. El experimento usa la distancia total y la subida acumulada del recorrido completo. Ambas variables se estandarizan con los parámetros archivados en `kmeans_k3_parametros_2026-11-10.json`. K-means forma tres grupos; se ordenan por la suma de las coordenadas estandarizadas de sus centroides: grupo 0 → **Fácil** (12 rutas), grupo 1 → **Moderada** (6) y grupo 2 → **Difícil** (2). Es una clasificación **relativa a estas 20 rutas y experimental**; el algoritmo no conoce el significado de esas palabras ni recibió etiquetas de expertos.

La interfaz lee las asignaciones archivadas y comprueba que sus 20 identificadores y sus valores de distancia y subida coincidan con el catálogo elegible. Una muestra distinta provoca un error en vez de reutilizar silenciosamente etiquetas antiguas. La regla de marcha inspirada en MIDE sigue disponible como contraste y para mostrar horas de referencia, pero **no asigna las categorías visibles**. Su reparto anterior fue 8/10/2. R004, R015, R023 y R026 pasan de Moderada en esa regla a Fácil en K-means.

## Por qué se informa como resultado experimental

El diseño del experimento fijó los criterios C1–C5 antes de observar los resultados. Según ellos, la decisión automática fue **B: no sustituir la regla como clasificación científica validada**. No se alteran esos criterios ni el informe original. La decisión posterior de mostrar K-means en el prototipo responde al objetivo de la tesis de comprobar un clasificador no supervisado de tres niveles, con sus límites a la vista:

- La partición 12/6/2 es igual en 50 semillas y tiene silueta 0,5895. Ward difiere en R022.
- El grupo Difícil se apoya solo en R001 y R006. Con el ascenso del DEM sin filtrar cambian R003, R015, R019 y R023; con pesos de estrés cambia R006; al añadir pendiente media cambia R022. Estos cambios generan los avisos de sensibilidad de la página. El DEM crudo es una prueba de estrés; una mediana de cinco puntos conserva la partición.
- DBSCAN se usa como contraste, pero no confirma tres grupos estables para las 20 rutas. La regla anterior coincide con K-means en 16 de 20 casos por orden; esa coincidencia no mide exactitud, porque no existe una verdad de terreno etiquetada.
- Los grupos dependen de esta muestra y de las variables elegidas. Agregar rutas exige reentrenar y revisar los nombres, la sensibilidad y los resultados de la página.

La etiqueta física no evalúa dificultad técnica, altitud, acceso, clima, estado del sendero, seguridad o aptitud de una persona. Esos aspectos se muestran por separado. La página no recomienda una salida. Para defender las palabras Fácil, Moderada y Difícil como niveles de validez externa faltan juicio de especialistas, percepción de esfuerzo de caminantes, más rutas de esfuerzo alto y contraste de perfiles de elevación.

## Reproducción y archivos

Ejecutar `06_scripts/evaluar_kmeans_k3_dificultad.py` para reproducir las tablas y el informe del experimento. `06_scripts/vista_rutas.py` lee las asignaciones y pruebas de sensibilidad; `app.py` presenta las categorías. El notebook `05_notebooks/05_validacion_metodologica.ipynb`, sección 11, conserva el experimento y su decisión científica histórica. La decisión posterior de interfaz se registra aquí y en el README; no convierte un criterio fallido en uno aprobado.
