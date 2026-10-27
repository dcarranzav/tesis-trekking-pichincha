# Guion de narración: video de presentación del proyecto

Video: `08_evidencias/rutas_trekking_pichincha_presentacion_2026-10-24.mp4` (2:50, 1920×1080, con música suave y sin voz).
El video funciona sin narración, porque todo el mensaje está en pantalla. Si lo presentas en vivo, baja la música y lee este guion. Cada bloque dura lo mismo que su escena.

| Tiempo | En pantalla | Qué decir |
|---|---|---|
| 0:00 | Título sobre imagen satelital del Rucu Pichincha | «Antes de salir a caminar, todos nos hacemos la misma pregunta: ¿qué tan exigente físicamente es esta ruta?» |
| 0:08 | Las tres preguntas | «¿Cuántos kilómetros son en total, contando el regreso? ¿Cuánto se sube y cuánto se baja? Y cuando una ruta dice “fácil”, ¿fácil según qué? Hoy esa información está dispersa y sin un criterio común.» |
| 0:18 | 20 rutas, una regla, tres niveles (8 / 10 / 2) | «Nuestro proyecto analiza 20 rutas de Pichincha, unos 70 km de trazado, con una misma regla. Cada ruta recibe una sola etiqueta: dificultad física estimada. Ocho son Fácil, diez Moderada y dos Difícil.» |
| 0:28 | Para quién es | «Está pensado para quien planifica una caminata: caminantes, clubes, guías y docentes, y también para turismo y gestión local, que necesitan informar con un criterio explicado.» |
| 0:39 | Paso 1: bienvenida | «Entrar es inmediato: se escribe un nombre y listo, sin cuentas ni contraseñas.» |
| 0:47 | Paso 2: tarjetas | «Se filtra por lugar, nombre o dificultad, y con “Ver ruta” se abre la ficha.» |
| 0:54 | Paso 3: ficha del Rucu Pichincha | «La ficha muestra una sola etiqueta, en este caso Difícil. Aparte van los avisos: aquí, alta montaña a unos 4 680 metros. No mezclamos la altitud ni el acceso con el esfuerzo.» |
| 1:04 | Paso 4: cifras y escala | «Se ven las cifras de la ruta completa: 9,61 km, 825 m de subida y 825 m de bajada. La escala dice dónde cae: 4,64 horas de esfuerzo estimado.» |
| 1:13 | Simulación en satélite | «Y esto es lo más llamativo: la ruta se puede recorrer antes de caminarla. Sobre imagen satelital, el punto avanza y el mapa lo sigue. La ida se pinta en naranja y el regreso en blanco.» |
| 1:28 | Perfil de altura | «El perfil de altura avanza junto al mapa: se ve dónde está la subida fuerte y dónde se da la vuelta.» |
| 1:36 | La regla | «La regla es pública y es la misma para todas: distancia entre 4 km/h, subida entre 400 m/h y bajada entre 600 m/h. Se toma el mayor más la mitad del menor. Hasta una hora es Fácil, hasta tres Moderada y más de tres Difícil. Se inspira en el componente de esfuerzo del método MIDE.» |
| 1:46 | Gráfico de horas | «Este es el resultado de las 20 rutas, ordenadas por esfuerzo. Las marcadas con asterisco cambian de categoría si se cambian los supuestos, y la página lo avisa.» |
| 1:57 | Avisos | «Fácil no significa segura. Por eso el acceso, la altitud y el carácter técnico van como avisos aparte, y cada trazado cita su fuente y su licencia.» |
| 2:08 | Comparar: Yellow House | «También se pueden comparar alternativas, pero solo entre rutas que llegan al mismo destino exacto, como los tres caminos a Yellow House.» |
| 2:17 | Lo que reúne en un solo lugar | «En resumen, la página reúne una regla única y explicada, la ruta completa con ida y regreso, la simulación sincronizada, los avisos separados y pruebas de sensibilidad con datos abiertos.» |
| 2:30 | Viabilidad | «¿Es viable? Sí. El método se puede repetir: usa OpenStreetMap y Copernicus, que cubren todo el Ecuador. El siguiente paso es sumar rutas en Pichincha, luego escalar a otras provincias y validar con caminatas reales y con usuarios. Como todo es abierto, crecer no implica pagar licencias.» |
| 2:42 | Cierre | «Rutas de trekking en Pichincha. Gracias.» |

## Preguntas probables del jurado

- **¿Qué viabilidad tiene?** El flujo es reproducible: se toman los trazados de OpenStreetMap y la elevación de Copernicus (cobertura mundial), y se aplica la misma regla. Agregar una ruta no exige reprogramar la página. Los datos y las herramientas son abiertos, así que no hay costo de licencias.
- **¿Qué tiene que no tenga otra página de rutas?** Una regla única y publicada para todas las rutas, las cifras del recorrido completo (ida y regreso), la simulación sincronizada mapa y perfil, los avisos separados de la categoría y la prueba de sensibilidad. Para comparar con una aplicación concreta, conviene revisarla antes de la defensa; el video no nombra otras plataformas.
- **¿Está validado?** Todavía no. Faltan la revisión por especialistas, la prueba de comprensión con usuarios y las comprobaciones de acceso en campo. Están en la hoja de ruta.
- **¿Por qué no usar K-means para las categorías?** K-means, Ward, DBSCAN y el índice HEN se usaron como contraste metodológico. Las tres categorías salen de una regla explicable, no de un agrupamiento.
