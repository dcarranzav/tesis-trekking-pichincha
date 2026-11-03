# Portada de «Explorar rutas» con galería de fotografías (2 de noviembre de 2026)

## Qué se hizo

La sección «Explorar rutas» abre con una portada de presentación:

- Titular («Elige tu próxima caminata sabiendo cuánto esfuerzo te espera»), una frase de apoyo, el botón «Explorar las 20 rutas» (baja a la lista) y las cifras por nivel (8 Fácil, 10 Moderada, 2 Difícil).
- **Galería interactiva** con las seis fotografías: pasan solas cada 5,5 s con fundido y un acercamiento lento; se puede elegir con las miniaturas, las flechas, el teclado (izquierda y derecha) o deslizando el dedo en el teléfono. Se detiene al pasar el cursor o al enfocarla. Si el navegador pide reducir el movimiento, no avanza sola ni hace zoom.
- Tres ventajas reales de la página: una sola regla para las 20 rutas, simulación del recorrido con perfil de altura y entrada con apodo, sin cuentas.

Las tarjetas de ruta no llevan fotografía. No cambian los indicadores, los niveles de dificultad, los filtros, las fichas, el mapa, el perfil, el clima ni las descargas.

## Criterio del texto

El texto vende lo que la página hace y se puede comprobar. No se usan «las mejores rutas», valoraciones, estrellas, popularidad, cifras de usuarios ni garantías de seguridad: eso no está respaldado por los datos del proyecto. La prueba `test_texto_de_venta_cumple_y_no_inventa` lo vigila. Las fotos son ambientación y no se asocian a rutas concretas; sus textos alternativos las describen sin nombrar lugares.

## Dónde están las fotos

Recortes horizontales de 960 x 540 px, optimizados para la web y sin metadatos EXIF, en `assets/fotos/`. Los originales (carpeta Descargas del autor) no se modificaron.

| Archivo web | Original | Personas visibles |
|---|---|---|
| `galeria_01.jpg` | WhatsApp Image 2026-11-02 at 20.09.24 | Sí (dos excursionistas de espaldas) |
| `galeria_02.jpg` | ...20.09.25 | No |
| `galeria_03.jpg` | ...20.09.26 | Sí (grupo en una ladera rocosa) |
| `galeria_04.jpg` | ...20.09.27 | No |
| `galeria_05.jpg` | ...20.09.28 | Sí (tres excursionistas de espaldas) |
| `galeria_06.jpg` | ...20.09.29 | Sí (silueta y personas al borde del encuadre) |

Código: `06_scripts/fotos_pagina.py` (lista, orden, textos alternativos y base64), `portada_marketing` y `galeria_interactiva` en `06_scripts/visuales_pagina.py`, y los estilos en `app.py`. Las imágenes se incrustan en el CSS, así funcionan con `streamlit run app.py` y en el despliegue, sin rutas de la computadora. Si una foto no carga, el recuadro queda con un degradado. Las versiones anteriores de las fotos quedaron en `_to_delete/`.

## Pendiente antes de publicar la página

Las fotografías son del autor y de sus amigos. Cuatro muestran personas (01, 03, 05 y 06): antes de publicar, confirmar con ellas que aceptan su uso público. Si alguna no acepta, reemplazar esa imagen en `assets/fotos/` y actualizar `fotos_pagina.py`.

## Pruebas

`tests/test_visuales_pagina.py` (clases `PortadaConFotosTest` y `PlantillaVisorCapasTest`) y `tests/test_app_humo.py`. La galería se probó además en un navegador real con una maqueta de la misma HTML y CSS: avance automático, miniaturas, flechas, pausa y deslizar. Falta comprobarla dentro de Streamlit real.
