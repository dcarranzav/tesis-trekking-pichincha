# Registro de descargas de elevación

Este documento conserva la procedencia y las comprobaciones de los archivos originales de elevación. Los archivos se almacenan sin modificaciones en `02_datos_originales/elevacion`.

## Copernicus DEM GLO-30 Public – mosaico S01 W079

- **Fecha de descarga:** 2026-10-05
- **Producto:** Copernicus Digital Elevation Model GLO-30 Public
- **Versión de distribución:** Copernicus DEM 2021
- **Archivo:** `Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif`
- **URL de descarga:** https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S01_00_W079_00_DEM/Copernicus_DSM_COG_10_S01_00_W079_00_DEM.tif
- **Formato:** Cloud Optimized GeoTIFF
- **Tamaño:** 41.363.224 bytes
- **SHA-256:** `09DCA8C4E872A804CACDC87084F32510AEC30B6AC18DA9E4D1F9D358D1488D4B`
- **Sistema de coordenadas:** EPSG:4326
- **Dimensiones:** 3600 × 3600 celdas
- **Resolución angular:** 0.0002777777777777778 grados, equivalente a 1 segundo de arco
- **Tipo de dato:** float32
- **Número de bandas:** 1
- **Extensión aproximada:** 79° O a 78° O y 1° S a 0°

## Cobertura del piloto

Se comprobó que el mosaico cubre completamente los trazados intermedios de R001, R003, R005 y R006. No fue necesario unir mosaicos adicionales para la fase piloto.

## Copernicus DEM GLO-30 Public – mosaico N00 W079

- **Fecha de descarga:** 2026-10-06
- **Producto:** Copernicus Digital Elevation Model GLO-30 Public
- **Versión de distribución:** Copernicus DEM 2021
- **Archivo:** `Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif`
- **URL de descarga:** https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N00_00_W079_00_DEM/Copernicus_DSM_COG_10_N00_00_W079_00_DEM.tif
- **Formato:** Cloud Optimized GeoTIFF
- **Tamaño:** 44.013.295 bytes
- **SHA-256:** `9F1FC1EF388645B60C9283DA9A71AF5399D8EB2ADF1AFD7EECA07D122805BCC7`
- **Sistema de coordenadas:** EPSG:4326
- **Dimensiones:** 3600 × 3600 celdas
- **Resolución angular:** 0.0002777777777777778 grados, equivalente a 1 segundo de arco
- **Tipo de dato:** float32
- **Número de bandas:** 1
- **Extensión aproximada:** 79° O a 78° O y 0° a 1° N

## Cobertura de la ampliación

R002 y R007 utilizan el mosaico S01 W079. R004 se encuentra al norte del ecuador y utiliza N00 W079. El script de ampliación selecciona explícitamente el mosaico correspondiente a cada ruta y comprueba que todos los puntos muestreados estén dentro de sus límites.

## Conservación

El archivo se utilizará únicamente como dato original de entrada. Cualquier perfil, tabla, recorte o transformación derivada se almacenará fuera de `02_datos_originales`.
