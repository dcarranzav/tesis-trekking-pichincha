# Fuente de datos de elevación

## 1. Fuente seleccionada

- **Producto:** Copernicus Digital Elevation Model GLO-30 Public
- **Versión de distribución:** Copernicus DEM 2021
- **Organismo responsable:** Programa Copernicus de la Unión Europea y Agencia Espacial Europea
- **Distribución utilizada:** Registry of Open Data on AWS
- **Resolución espacial aproximada:** 30 m
- **Resolución angular:** 1 segundo de arco
- **Formato:** Cloud Optimized GeoTIFF
- **Fecha de consulta:** 2026-10-05
- **Documentación:** https://copernicus-dem-30m.s3.amazonaws.com/readme.html
- **Registro de descarga:** https://registry.opendata.aws/copernicus-dem/
- **Licencia:** https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM

## 2. Justificación

Copernicus DEM GLO-30 Public proporciona una cobertura consistente y una resolución aproximada de 30 m, adecuada para estimar perfiles altitudinales e indicadores físicos de rutas de trekking a escala provincial.

Los datos se distribuyen como archivos GeoTIFF que pueden conservarse localmente junto con el proyecto. Esto permite documentar el archivo utilizado, repetir el procesamiento y aplicar la misma fuente de elevación a todas las rutas.

El entorno del proyecto dispone de Rasterio, por lo que los valores del modelo pueden consultarse directamente desde Python sin depender de una API externa durante cada ejecución.

## 3. Limitaciones

Copernicus DEM es un modelo digital de superficie y no un modelo puro del terreno. Sus valores pueden representar la parte superior de la vegetación, edificios u otras estructuras presentes sobre el suelo.

Esta limitación deberá considerarse especialmente en rutas de bosque nublado, como R005. Los perfiles serán revisados para identificar cambios abruptos, valores faltantes o variaciones incompatibles con la forma general del recorrido.

La resolución de aproximadamente 30 m tampoco permite representar todos los cambios pequeños del sendero. Por esta razón, los resultados se interpretarán como estimaciones de la dificultad física y no como mediciones topográficas de precisión.

## 4. Uso previsto

El modelo se utilizó inicialmente con las cuatro rutas piloto y se mantiene como fuente común durante la ampliación. Para cada ruta se comprueban:

- cobertura completa del trazado;
- valores de elevación no vacíos;
- elevación mínima y máxima;
- coherencia general del perfil;
- cambios altitudinales abruptos;
- sensibilidad del ascenso acumulado al procedimiento de muestreo y limpieza.

El procedimiento se estabilizó con el piloto antes de aplicarlo a las rutas adicionales. Cuando una ruta cruza el límite de un mosaico de un grado, se incorpora el archivo contiguo y se registra individualmente su URL, tamaño, hash y cobertura.

## 5. Atribución

Copernicus Digital Elevation Model (DEM), versión 2021, consultado el 5 de octubre de 2026 mediante Registry of Open Data on AWS: https://registry.opendata.aws/copernicus-dem/
