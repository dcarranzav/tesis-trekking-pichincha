# Informe de auditoría integral del proyecto (2026-10-24)

## Resultado ejecutivo

- Controles ejecutados: **272**.
- Controles correctos: **272**.
- Errores estructurales: **0**.
- Advertencias: **0**.
- Rutas procesadas: **27**.
- Rutas elegibles para el modelo: **20**.
- Rutas aún no elegibles: **7** (R002, R005, R007, R009, R010, R012, R014).

La auditoría valida la integridad técnica del estado actual. No constituye validación externa: la clasificación principal de tres niveles tiene método y sensibilidad separados, pero no habilita recomendaciones de salida.

## Alcance verificado

- Concordancia de identificadores entre inventario y dataset maestro.
- Unicidad del nombre por destino y exclusión de rutas técnicas del conjunto elegible.
- Existencia de archivos fuente declarados y DEM utilizados; contraste del XML OSM exacto de R022, R023, R024/R025, R026 y R027, incluidos sus extremos y continuidad declarados.
- Un GeoJSON por ruta, con LineString simple, válida y en EPSG:4326.
- Perfiles raw y procesados, número de puntos, ausencia de vacíos y reconciliación de elevaciones y distancia.
- Figura SVG por ruta.
- Evidencias PNG registradas sin archivos huérfanos.
- Sintaxis de scripts Python y de todas las celdas de código de los notebooks, además de su estructura JSON.
- Dependencias principales y documentación metodológica.

## Hallazgos que todavía requieren trabajo

- R001: elegible en el conjunto actual por la variante del arenal según I10/E10; el tramo T3 y la altitud se documentan como riesgos, no como exclusión automática ni como certificación de seguridad. R007 sigue pendiente de evidencia temática.
- R002: confirmar documentalmente la identidad del trazado como Los Pantzas.
- R005: la línea pasa a 106.5 m de Cascada Nambillo, pero su final queda a 443.3 m; confirmar el recorrido correcto.
- R009 y R010: los extremos medidos y las fuentes históricas no acreditan recorridos completos; obtener mapa o track nominal vigente y confirmar el acceso antes de incorporarlas al modelo.
- R012 y R014 Yanacocha: excluidas provisionalmente del modelo hasta verificar identidad y extremos con mapa o track nominal vigente; se conservan sus originales y perfiles. R011 y R013 también requieren comprobación del recorrido completo.
- R021 Yellow House: confirmar con el operador si Senderos 1 y 2 están abiertos y si la variante combinada representa una alternativa independiente; su elegibilidad es solo provisional.
- R022 Cruz del Ilaló: el XML íntegro ya está archivado y concuerda con la instantánea normalizada; dos nodos de la vía figuran como `ford=yes`. Verificar los posibles vados, la apertura pública y las condiciones de acceso antes de recomendarla.
- Diversidad de la muestra: 7 de 20 rutas elegibles pertenecen a los dos lugares amplios (`id_destino`) más representados, que pueden contener llegadas distintas; evaluar su efecto en los grupos.
- Con 20 elegibles se alcanzó la meta mínima de 20 y la regla de dificultad física estimada ya fue evaluada por separado. Sus tres niveles pueden comunicarse con sus límites y casos sensibles; no habilitan recomendaciones automáticamente.

## Reproducción

Ejecutar desde la raíz del repositorio:

```powershell
C:\Users\LENOVO\miniforge3\envs\trekking_pichincha\python.exe 06_scripts/auditar_integridad_proyecto.py --fecha 2026-10-24
```

La tabla detallada se guarda en `07_resultados/tablas/auditoria_integridad_proyecto.csv`.
