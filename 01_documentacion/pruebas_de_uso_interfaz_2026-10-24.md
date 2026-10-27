# Recorrido de uso de la interfaz — 24 de octubre de 2026

Se probó `app.py` en Streamlit real (`http://127.0.0.1:8501/`) mediante un recorrido guiado que simula tareas de una persona sin conocimientos geoespaciales. **No participaron usuarios externos**; esta revisión no sustituye la prueba de comprensión prevista en la tesis.

| Tarea simulada | Resultado observado |
| --- | --- |
| Entrar sin nombre y luego con un nombre usando Enter | El nombre vacío muestra una indicación clara y mantiene cerrada la exploración. Con un nombre aparece el saludo y la lista de rutas. |
| Buscar «Guarumos», abrir la ficha y volver | La búsqueda deja una ruta; la ficha muestra dificultad, mapa, perfil, avisos y descargas. El regreso conserva el filtro, por lo que el botón ahora dice «Volver a la lista». |
| Comparar Yellow House y fijar una distancia máxima de 5,6 km | Se muestran tres rutas al mismo destino exacto; la tabla y las barras cambian con el destino. El filtro indica que coincide Yellow House Trail sin ocultar las otras alternativas. Se puede abrir una ruta desde la comparación. |
| Consultar clima en la ficha | Open-Meteo respondió con temperatura, precipitación y viento separados para inicio y llegada. El resultado ahora queda visible aunque el desplegable se cierre al volver a ejecutar Streamlit. |
| Usar el visor en 390 × 844 px | Mapa, capas, seguimiento, reproducción y pausa funcionaron. Se separaron los controles de capas y seguimiento para evitar superposición. No se detectó desbordamiento horizontal (`scrollWidth` de página: 390 px). |
| Leer metodología y una ruta cercana al umbral de 1 h | Se identificó que 1,0113 h y 1,0168 h aparecían como «1,0 h · Moderada». Se muestran ahora como 1,01 h y 1,02 h; la regla y las categorías archivadas no cambiaron. |

Se redujo la portada en las secciones secundarias para que comparación y metodología empiecen con su propio contenido. Las capturas de Streamlit real están en `08_evidencias/prueba_uso_bienvenida_streamlit_real_2026-10-24.png`, `08_evidencias/prueba_uso_ficha_movil_streamlit_real_2026-10-24.png` y `08_evidencias/prueba_uso_metodologia_movil_streamlit_real_2026-10-24.png`.

El ingreso pide obligatoriamente un nombre, pero es una identificación temporal de la sesión: no crea una cuenta ni conserva un registro al cerrar la pestaña. Si el producto final requiere cuentas persistentes, ese requisito necesita una definición aparte de datos y acceso.

**Verificación técnica:** 101 pruebas enfocadas en aplicación, visuales, clima y rutas pasaron. La suite completa cerró con **208 pruebas correctas** en el entorno Miniforge del proyecto, usando `MKL_THREADING_LAYER=SEQUENTIAL` y un hilo para MKL, OpenBLAS y OpenMP durante la ejecución. La auditoría de integridad cerró con **272 controles correctos**, sin advertencias ni errores. Falta la prueba con personas reales y la comprobación en un teléfono físico.

Comando reproducible para la suite completa en PowerShell:

```powershell
$env:MKL_THREADING_LAYER = 'SEQUENTIAL'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
& 'C:\Users\LENOVO\miniforge3\envs\trekking_pichincha\python.exe' -m unittest discover -s tests -q
```

## Guion pendiente para participantes reales

Dar a cada participante la página sin instrucciones sobre dónde hacer clic. Pedirle que: (1) ingrese su nombre; (2) encuentre una ruta Fácil y explique qué significa esa etiqueta; (3) compare las rutas a Yellow House; (4) abra una ficha y diga si la ruta está confirmada como abierta; (5) consulte el clima y explique si 20 °C puede coincidir con lluvia. Registrar si completó cada tarea sin ayuda, qué texto interpretó mal y en qué paso dudó. Al terminar, preguntar si usaría la categoría para decidir salir sin revisar otra fuente. Hacerlo con varias personas ajenas al proyecto, incluyendo al menos una en teléfono físico; no anotar nombres completos ni datos personales en el informe de resultados.
