# Criterios de selección y calidad de las rutas

## 1. Propósito y alcance

Este documento establece los criterios que se utilizarán para identificar, revisar, incluir o excluir rutas de trekking en la provincia de Pichincha.

La unidad de análisis será una **alternativa de ruta de trekking** representada mediante un trazado geoespacial digital. Un mismo destino podrá tener varias alternativas únicamente cuando sus trazados, puntos de inicio o características físicas sean realmente diferentes. Cada alternativa deberá contar con información suficiente para calcular indicadores relacionados con la distancia, la elevación, el desnivel positivo acumulado y la pendiente.

La selección busca construir un conjunto de datos consistente, reproducible y adecuado para caracterizar y clasificar la dificultad física estimada de las rutas.

La clasificación resultante se limitará a la exigencia física estimada de rutas no técnicas. No evaluará seguridad, estado del sendero, condiciones meteorológicas, accesibilidad ni riesgos naturales. Esos elementos podrán mostrarse como información complementaria en la interfaz, pero no se mezclarán con el agrupamiento físico.

### 1.1 Destino, alternativa y actividad compatible

- **Destino:** lugar de interés al que el usuario desea llegar, por ejemplo una laguna, cascada, refugio, mirador o sector recreativo.
- **Alternativa de ruta:** recorrido geoespacial concreto para llegar al destino o completar un circuito. Cada alternativa recibe un `id_ruta` independiente.
- **Actividad compatible:** caminata, senderismo o trekking no técnico. La altitud elevada por sí sola no excluye una ruta; lo determinante es si exige escalada, progresión glaciar o equipo técnico especializado.
- **Actividad por verificar:** recorrido cuya descripción no permite confirmar todavía si es trekking no técnico. Se conserva en el inventario, pero no entra al entrenamiento hasta resolver la duda.

## 2. Criterios de inclusión

Para ser incorporada al conjunto de datos, una ruta deberá cumplir todos los criterios siguientes:

- **I01. Ubicación geográfica:** el trazado deberá localizarse dentro de los límites administrativos de la provincia de Pichincha.
- **I02. Tipo de actividad:** la ruta deberá corresponder a una actividad de trekking, senderismo o caminata recreativa realizada principalmente a pie.
- **I03. Trazado disponible:** deberá existir un trazado geoespacial descargable o reproducible con coordenadas ordenadas del recorrido.
- **I04. Fuente identificable:** deberán registrarse la fuente, el enlace o identificador y la fecha de consulta.
- **I05. Uso permitido:** la licencia o las condiciones de la fuente deberán permitir su utilización académica y la elaboración de productos derivados, incluyendo la atribución cuando corresponda.
- **I06. Geometría utilizable:** el trazado deberá tener continuidad suficiente para representar el recorrido después de aplicar los procedimientos de revisión y limpieza.
- **I07. Elevación obtenible:** el trazado deberá contener datos de elevación o permitir obtenerlos mediante una fuente de elevación externa.
- **I08. Indicadores calculables:** deberá ser posible calcular la distancia, la elevación mínima y máxima, el desnivel positivo acumulado y los indicadores de pendiente.
- **I09. Ruta diferenciable:** la ruta no deberá ser un duplicado de otra. Las variantes podrán conservarse únicamente cuando representen recorridos claramente diferentes y queden documentadas.
- **I10. Compatibilidad no técnica:** deberá existir evidencia suficiente de que la alternativa puede recorrerse principalmente a pie sin escalada, progresión glaciar ni equipo técnico especializado obligatorio.
  Una etiqueta de senderismo de montaña exigente (`sac_scale=demanding_mountain_hiking`, T3) no implica por sí sola inclusión ni exclusión: se contrasta el trazado concreto con fuentes sobre escalada y equipo obligatorio. La exposición, la altitud y otros riesgos se documentan aparte; la elegibilidad para analizar esfuerzo físico no certifica seguridad ni aptitud para todos los usuarios.

## 3. Criterios de exclusión

Una ruta se excluirá del conjunto final de análisis cuando presente al menos una de las siguientes condiciones:

- **E01. Fuera del área de estudio:** el trazado se encuentra fuera de los límites administrativos de la provincia de Pichincha.
- **E02. Actividad incompatible:** el recorrido corresponde principalmente a ciclismo, conducción motorizada, competencia vehicular u otra actividad diferente del trekking o senderismo a pie.
- **E03. Trazado no disponible:** no existe un archivo geoespacial descargable ni un procedimiento razonable para reproducir el recorrido.
- **E04. Fuente no verificable:** no es posible identificar o documentar el origen del trazado después de revisar la información disponible.
- **E05. Uso no permitido:** la licencia o las condiciones de la fuente impiden su utilización académica o la generación de productos derivados.
- **E06. Geometría no recuperable:** el archivo está vacío, corrupto, presenta interrupciones graves o contiene errores que impiden reconstruir el recorrido de manera confiable.
- **E07. Ruta duplicada:** el trazado representa el mismo recorrido que otra ruta ya seleccionada y no constituye una variante suficientemente diferente.
- **E08. Elevación no obtenible:** no es posible obtener datos de elevación con calidad suficiente para calcular los indicadores requeridos.
- **E09. Indicadores no confiables:** después de la limpieza y revisión, los resultados presentan valores incoherentes o insuficientes para caracterizar la ruta.
- **E10. Actividad técnica:** el recorrido exige escalada, progresión por glaciar, cuerda, crampones, piolet u otro equipo técnico obligatorio. Los ascensos de alta montaña permanecerán `por_verificar` mientras esa condición no pueda establecerse documentalmente.

Las rutas excluidas no se eliminarán del inventario. Se conservarán con la decisión correspondiente y con una explicación en el campo `motivo_decision`.

## 4. Criterios de calidad del trazado

Cada ruta será sometida a una revisión de calidad antes de incorporarla al análisis. La revisión considerará los siguientes aspectos:

- **Q01. Procedencia documentada:** la fuente, el enlace o identificador, la fecha de consulta y las condiciones de uso están registrados.
- **Q02. Archivo legible:** el archivo puede abrirse correctamente y contiene una geometría no vacía.
- **Q03. Coordenadas válidas:** las coordenadas se encuentran dentro de rangos geográficos válidos y corresponden al área de estudio.
- **Q04. Sistema de referencia identificable:** el sistema de coordenadas puede determinarse y transformarse cuando sea necesario.
- **Q05. Continuidad del recorrido:** el orden de los puntos representa un desplazamiento continuo y no contiene saltos espaciales injustificados.
- **Q06. Geometría consistente:** el trazado no contiene segmentos vacíos, puntos aislados anómalos ni errores graves de construcción.
- **Q07. Resolución espacial suficiente:** la cantidad y distribución de puntos permiten representar adecuadamente la forma y longitud del recorrido.
- **Q08. Elevación suficiente:** existe información de elevación para una proporción adecuada de los puntos del trazado.
- **Q09. Elevación coherente:** el perfil no presenta valores imposibles, cambios abruptos injustificados ni vacíos que impidan calcular el desnivel positivo acumulado.
- **Q10. Indicadores plausibles:** la distancia, las elevaciones y las pendientes obtenidas son coherentes con el recorrido y el contexto geográfico.
- **Q11. Ausencia de duplicidad:** el trazado no reproduce otra ruta ya incorporada sin una diferencia relevante y documentada.

### 4.1 Clasificación preliminar de la calidad

El campo `calidad_preliminar` utilizará las siguientes categorías:

- **pendiente:** la ruta todavía no ha sido revisada.
- **apta:** cumple los controles críticos y puede utilizarse en el análisis.
- **dudosa:** presenta anomalías o información incompleta que requieren revisión manual antes de tomar una decisión.
- **no_apta:** presenta problemas críticos que impiden obtener resultados confiables.

Los problemas detectados, las correcciones realizadas y las decisiones adoptadas deberán registrarse en los campos `motivo_decision` y `observaciones` del inventario.

Los umbrales cuantitativos para detectar saltos espaciales, vacíos de elevación, pendientes extremas y otros valores anómalos se comprobarán inicialmente con las rutas piloto. Cualquier ajuste deberá documentarse y aplicarse posteriormente de manera uniforme a todas las rutas.

## 5. Reglas para la decisión final

Después de revisar los criterios de selección y calidad, cada ruta recibirá uno de los siguientes valores en el campo `decision`:

- **pendiente:** la ruta está registrada, pero todavía no ha completado el proceso de revisión.
- **incluir:** cumple todos los criterios de inclusión, presenta calidad apta y permite calcular indicadores confiables.
- **excluir:** incumple uno o más criterios esenciales relacionados con el área de estudio, el tipo de actividad, la fuente, las condiciones de uso, la geometría o la duplicidad.
- **excluir_provisional:** el trazado y los indicadores se conservan, pero una duda documentada sobre identidad, extremos o alcance turístico impide usar esa observación en el modelo por ahora. Puede revertirse únicamente después de una verificación con fuente identificable y de regenerar el conjunto maestro.
- **no_clasificable:** pertenece al ámbito del estudio y dispone de un trazado identificable, pero después de la revisión y limpieza no permite calcular con suficiente confiabilidad los indicadores necesarios para clasificar su dificultad física estimada.

Una ruta con calidad `dudosa` mantendrá la decisión `pendiente` o `excluir_provisional` hasta completar su revisión manual; ninguno de esos estados la vuelve elegible.

Una ruta con `comparable_trekking=por_verificar` tampoco podrá usarse para ajustar el modelo, aunque su geometría y perfil de elevación sean correctos. Esta separación evita confundir calidad cartográfica con compatibilidad temática.

Cuando un problema pueda corregirse sin alterar de manera injustificada el recorrido, el archivo corregido se guardará en `03_datos_intermedios`. El archivo original se conservará sin modificaciones en `02_datos_originales`.

Toda decisión deberá estar acompañada por una explicación breve y verificable en el campo `motivo_decision`. Cuando sea necesario, los detalles adicionales se registrarán en `observaciones`.
