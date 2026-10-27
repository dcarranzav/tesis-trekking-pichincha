# Prompt para Claude: interfaz final alineada con el plan de tesis

Trabaja sobre este repositorio existente. Antes de editar, lee completos `README.md`, `01_documentacion/clasificacion_dificultad_fisica_tres_niveles_2026-10-23.md`, `01_documentacion/alineacion_plan_tesis_interfaz_2026-10-22.md`, `01_documentacion/interfaz_publica_2026-10-21.md`, `06_scripts/vista_rutas.py`, `app.py`, `web/app.py` y las pruebas de interfaz. No modifiques los datos científicos, inventarios, scripts de procesamiento, notebooks ni resultados de clasificación.

## Resultado científico que la interfaz debe comunicar

El objetivo central de la tesis es clasificar la **dificultad física estimada** de rutas de trekking de Pichincha y apoyar su consulta. La clasificación pública final tiene exactamente tres categorías: **Fácil, Moderada y Difícil**. La regla está calculada y archivada; no debes recalcularla en la interfaz ni crear otro puntaje.

Usa `vista_rutas.dificultad_fisica_estimada(id_ruta)` y la tabla vigente `07_resultados/tablas/clasificacion_dificultad_fisica_2026-10-23.csv`. El resultado base de las 20 rutas elegibles es 8 Fácil, 10 Moderada y 2 Difícil. Seis rutas son sensibles a supuestos (`R003`, `R004`, `R008`, `R019`, `R025`, `R026`); muestra un aviso sobrio como «La categoría cambia en algunos escenarios metodológicos» dentro del detalle de esas rutas.

La regla está inspirada en el componente de cantidad de esfuerzo de MIDE, pero **no es el MIDE completo**. No clasifica dificultad técnica, orientación, severidad del medio, acceso actual, seguridad ni adecuación para una persona concreta. K-means k=2, Ward, DBSCAN y el índice HEN son contrastes metodológicos; no deben aparecer como otra categoría, medalla, ranking o recomendación en la vista principal.

## Arquitectura de la experiencia

1. La portada debe responder en lenguaje común: «¿Qué tan exigente físicamente es esta ruta?» y explicar que el usuario puede explorar 20 rutas mediante indicadores calculados de forma consistente.
2. La vista principal debe ser **Explorar rutas**, no «comparar alternativas». Permite filtrar por lugar, nombre y dificultad, y presenta tarjetas consistentes con nombre, categoría, distancia, ascenso y un aviso solo cuando corresponda.
3. La comparación debe ser una función secundaria llamada **Comparar alternativas**. Solo compara rutas que llegan al mismo destino exacto. Actualmente existen tres destinos con varias alternativas: Yellow House (3), Yanacocha (2) y Mirador Cerro de la Luz (2). Si un destino tiene una ruta, indícalo sin fabricar alternativas.
4. Incluye una sección **Cómo se calculó** o **Metodología y límites**, breve para público general y ampliable, que explique distancia, ascenso/descenso, regla de esfuerzo, categorías, sensibilidad y validación pendiente.
5. Mantén mapa, perfil altimétrico, simulación, descargas GeoJSON/GPX, atribuciones y fuentes existentes. No presentes el GPX como grabación GPS de campo ni como navegación en tiempo real.

## Lenguaje y jerarquía visual

- No muestres códigos como `R015` al usuario normal. Usa el nombre comprensible de la ruta. Los identificadores internos pueden permanecer en descargas, fuentes o detalle técnico.
- Muestra una sola etiqueta principal: «Dificultad física estimada: Fácil/Moderada/Difícil».
- Separa dificultad física de advertencias de altitud, acceso, carácter técnico o trazado pendiente de corroboración. Una categoría Fácil no significa segura ni abierta.
- Elimina emojis decorativos (reloj, nube, advertencia, montaña, etc.). Usa iconos SVG sobrios y coherentes solo cuando aporten información; también puede usarse texto sin icono.
- Todas las tarjetas del mismo conjunto deben tener igual altura, alineación y espaciado. En escritorio usa una cuadrícula estable; en móvil, una columna. Evita disposiciones 2+1 visualmente huérfanas.
- Usa una paleta profesional y accesible, buen contraste, tipografía consistente y estados que no dependan solo del color. No uses estética de chat o de contenido «generado por IA».
- La persona debe escribir su nombre para comenzar a explorar. Consérvalo solo durante la visita mediante `session_state`. No simules una cuenta, contraseña ni una base de datos inexistente.

## Clima

El clima es secundario, opcional y debe ir en una sección inferior o plegable. Preséntalo como estimación de un modelo externo, con lugar/coordenadas, hora de validez, fuente e intervalo temporal. Temperatura y precipitación son variables distintas: por ejemplo, **20,7 °C y lluvia pueden coexistir**; no traduzcas automáticamente esa temperatura como «calor» ni uses una sola etiqueta que mezcle ambas variables. Si la consulta falla, la exploración de rutas debe seguir funcionando.

## Restricciones científicas y funcionales

- No cambies umbrales, categorías, elegibilidad ni datos para mejorar la apariencia.
- No fuerces `k=3` ni uses K-means para generar Fácil/Moderada/Difícil.
- No habilites recomendaciones de salida. Conserva la puerta actual bloqueada y sus pruebas.
- No afirmes validación externa: aún faltan revisión por especialistas, prueba de comprensión con usuarios y varias comprobaciones de acceso/campo.
- No mezcles destinos cercanos para aumentar el número de alternativas.
- No publiques, no hagas push y no cambies infraestructura externa.

## Criterios de aceptación

1. `app.py` y `web/app.py` muestran exactamente la misma lógica principal de tres niveles y consumen la función central de `vista_rutas.py`.
2. Las 20 rutas tienen una categoría; se observan 8 Fácil, 10 Moderada y 2 Difícil; ninguna recomendación queda habilitada.
3. La página principal no muestra códigos `R###`, emojis decorativos ni la clase K-means.
4. Las tarjetas mantienen dimensiones coherentes en escritorio y móvil.
5. La comparación valida destino exacto y funciona para 3/2/2 alternativas.
6. El clima explica por separado temperatura y precipitación y tolera fallos de red.
7. Mapa, perfil, simulación, descargas, atribuciones y avisos por ruta siguen funcionando.
8. Actualiza o añade pruebas unitarias y de Streamlit para lo anterior. Ejecuta la suite completa y la auditoría del proyecto.
9. Revisa visualmente al menos una pantalla de escritorio y una móvil y guarda capturas en `08_evidencias` con fecha y nombres descriptivos.

Al terminar, entrega un resumen de archivos cambiados, decisiones de diseño, resultados exactos de pruebas/auditoría y cualquier limitación que siga pendiente. No declares completada la validación con expertos o usuarios si no se realizó realmente.
