# Demostración y publicación de la página

> **Actualización del 23 de octubre:** antes de publicar, aplicar `prompt_claude_interfaz_plan_final_2026-10-23.md`. La salida pública será Fácil/Moderada/Difícil; las referencias posteriores a dos clases K-means describen el corte anterior y no la interfaz final.

## Para quién es y qué resuelve

La página se dirige a personas que quieren explorar caminatas no técnicas en Pichincha y comparar recorridos que llegan **al mismo destino**. Reúne en un solo lugar el mapa, la distancia, el ascenso, un indicador comparativo de esfuerzo y las advertencias conocidas. La persona escribe su nombre para comenzar; no necesita entender datos geoespaciales ni crear una cuenta. El nombre se conserva solo durante la visita.

La página **no certifica la apertura, seguridad o aptitud personal**, no reemplaza a un guía ni a información oficial y no recomienda una ruta ganadora. Cada alternativa muestra una **clase física relativa** (menor o mayor exigencia física estimada) calculada con K-means sobre distancia total y ascenso de las 20 rutas estudiadas (`01_documentacion/informe_modelo_kmeans_fisico_2026-10-22.md`); no mide seguridad, acceso ni técnica, y R017, R019, R020 y R021 llevan aviso de sensibilidad. Ward y DBSCAN son contrastes metodológicos. El índice HEN es una referencia calculada, no un tiempo medido.

## Demostración local para el tutor

Desde la raíz del proyecto, en PowerShell con el entorno `trekking_pichincha` activo:

```powershell
python -m streamlit run app.py
```

Abrir la dirección que imprima Streamlit (habitualmente `http://localhost:8501`). Mostrar: 1) selección de lugar y destino exacto, 2) alternativas del mismo destino y límites personales de distancia/ascenso, 3) mapa y simulación de ida/regreso, 4) perfil y avisos, 5) descarga GPX. El clima es opcional: pulsar «Consultar clima de esta ruta» con internet; si el proveedor no responde, el resto sigue disponible. Si el tutor pregunta por K-means, abrir «¿Qué significa la clase física relativa?» (qué sí y qué no significa cada clase) y, en una ruta con aviso como R017, el detalle técnico con la sensibilidad.

Ejemplo útil: **Mindo → Yellow House** reúne R017, R021 y R020. Para mostrar dos trazados distintos al mismo mirador puede usarse **Puéllaro → Mirador Cerro de la Luz** (R024/R025), con sus advertencias de acceso visibles. No presentar las 20 rutas elegibles como 20 rutas abiertas o recomendadas.

## Publicar en Streamlit Community Cloud

La raíz contiene `environment.yml` para investigación y `requirements.txt` para una instalación ligera. Community Cloud prioriza `environment.yml` si ambos están en el mismo directorio. Por eso el punto de entrada de despliegue es **`web/app.py`**, junto a **`web/requirements.txt`**. Se verificó con `AppTest` que el punto de entrada carga la página sin excepciones. No requiere base de datos ni claves para el clima no comercial.

1. Revisar archivos y permisos antes de compartir el repositorio; subir los cambios necesarios a un repositorio GitHub bajo control del estudiante. Aún no hay remoto configurado ni se ha publicado la página.
2. Entrar en [Streamlit Community Cloud](https://share.streamlit.io/), conectar GitHub y elegir **Create app**.
3. Indicar repositorio, rama y archivo principal **`web/app.py`**. Elegir una versión de Python compatible con `streamlit>=1.66` y la misma versión probada localmente si está disponible.
4. Esperar la compilación; probar lugar, destino, cambio de alternativa, mapa, GPX y clima. Si el despliegue falla, revisar los registros de Cloud y confirmar que eligió `web/requirements.txt`.
5. Compartir la URL resultante con el tutor. Una aplicación procedente de repositorio privado necesita configuración explícita de visibilidad o invitación.

El visor Leaflet se distribuye dentro de `06_scripts/visor_ruta`; los mapas base se cargan por internet. Los archivos de perfiles, trazados, tablas y catálogos se leen del repositorio. **No subir solo `web/`: el despliegue necesita todo el proyecto.**

## Clima por ruta

La consulta opcional usa [Open-Meteo Forecast API](https://open-meteo.com/en/docs) en el inicio y la llegada; en circuitos usa el inicio y el punto más alto. Consulta temperatura, precipitación, viento y código meteorológico, indicando la hora local de validez. Envía la elevación DEM para el ajuste estadístico del modelo. La respuesta procede de **modelos meteorológicos, no de sensores instalados en el sendero**; su celda puede quedar a kilómetros del punto pedido y el tiempo puede variar rápidamente en montaña. La consulta falla de forma controlada sin afectar mapa o perfiles.

El acceso gratuito de Open-Meteo exige [uso no comercial y atribución](https://open-meteo.com/en/terms). Si la página se convierte en servicio comercial habrá que contratar la licencia correspondiente. La prueba real desde este equipo confirmó respuesta HTTPS para R017 el 22 de octubre; no implica garantía de disponibilidad futura.

## Pendientes antes del 27

- Revisar diseño y lenguaje con usuarios no técnicos; conservar la separación entre dato, estimación y advertencia.
- Ejecutar la página publicada desde otro dispositivo y documentar capturas reales de escritorio y móvil.
- Repetir suite y auditoría al congelar la página; reejecutar notebooks si cambian datos o métodos, no solo el diseño. La salida pública vigente es la regla de tres niveles; K-means queda únicamente como contraste metodológico. Ninguno debe presentarse como certificación de seguridad ni recomendación de salida mientras persistan las condiciones de acceso pendientes.

## Requisitos aún no cumplidos para publicar (al 23 de octubre)

- No hay repositorio remoto configurado ni URL publicada; hasta comprobar una URL funcional no debe afirmarse que el sitio está en línea.
- `02_datos_originales/elevacion` contiene dos mosaicos Copernicus `.tif` (≈44 MB y ≈41 MB) que la página **no usa** (lee perfiles ya procesados). Valorar excluirlos del repositorio público o usar Git LFS; si se publican, conservar la atribución Copernicus.
- El 23 de octubre se ejecutaron **13 pruebas de interfaz con Streamlit real** sin fallos dentro de una suite completa. En navegador local se inspeccionaron las tres secciones, la identificación temporal y el bloque de avisos en escritorio y con viewport de 390 × 844 px. No se observó desbordamiento horizontal. Esto **no equivale a probar un teléfono físico** ni el despliegue público; ambos siguen pendientes.
- La verificación técnica posterior al ajuste pasó **198/198 pruebas** y **272/272 controles** de auditoría, sin errores ni advertencias.
- Revisar `git status`: hay muchos archivos nuevos sin versionar; subir solo lo necesario y no incluir `_tmp/` ni `_to_delete/` (ya están en `.gitignore`).
