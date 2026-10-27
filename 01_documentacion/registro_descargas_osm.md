# Registro de descargas de OpenStreetMap

Este documento conserva las consultas utilizadas para obtener los trazados originales del proyecto. Los archivos descargados se guardan sin modificaciones en `02_datos_originales/trazados`.

## R001 – Sendero Cumbre Rucu Pichincha

- **Fecha de descarga:** 2026-09-30
- **Fuente:** OpenStreetMap mediante Overpass Turbo
- **Licencia:** Open Database License (ODbL) 1.0
- **Archivo obtenido:** `R001_rucu_pichincha_osm_2026-09-30.geojson`
- **Contenido:** 7 geometrías LineString correspondientes al trazado de subida
- **Uso posterior:** el recorrido de ida y vuelta se construirá en los datos intermedios; el archivo original no será modificado

### Consulta Overpass

```overpass
[out:json][timeout:60];

(
  way(377339148);
  way(377342076);
  way(377342086);
  way(377342089);
  way(377354725);
  way(377359598);
  way(442211574);
);

out meta geom;
```

### Descarga complementaria: conexión con Cruz Loma

- **Archivo obtenido:** `R001_conexion_cruz_loma_osm_2026-09-30.geojson`
- **Contenido:** 3 geometrías LineString que conectan el trazado inicial con el complejo del TelefériQo en Cruz Loma
- **Vías OSM:** 327805695, 377354721 y 377354724
- **Motivo:** durante la inspección se comprobó que el archivo inicial comenzaba después de Cruz Loma; este archivo conserva por separado los segmentos faltantes

```overpass
[out:json][timeout:60];

(
  way(327805695);
  way(377354721);
  way(377354724);
);

out meta geom;
```

### Resultado de R001

- **Segmentos originales usados inicialmente:** 10
- **Geometría intermedia:** LineString válida y continua
- **Distancia inicial de subida:** 4.436 km
- **Resultado de la revisión:** se detectó que el trazado terminaba antes del nodo de la cumbre

### Descarga complementaria: conexión final con la cumbre

- **Fecha de descarga:** 2026-10-05
- **Archivo obtenido:** `R001_conexion_cumbre_osm_2026-10-05.osm`
- **Vía OSM:** 377339146, `Arenal Bajada`
- **Nodo de cumbre:** 249414034, `Rucu Pichincha`, elevación OSM 4696 m
- **URL de descarga:** https://api.openstreetmap.org/api/0.6/way/377339146/full
- **Resultado corregido:** 11 segmentos, 4.804 km de subida y 9.607 km de ida y vuelta

## R002 – Candidato Sendero Los Pantzas

- **Fecha de descarga:** 2026-10-06
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Archivo del acceso:** `R002_pantzas_acceso_osm_2026-10-06.osm`
- **Archivo principal:** `R002_pantzas_principal_osm_2026-10-06.osm`
- **Formato original:** OSM XML
- **Vías utilizadas:** 256471445 y 205097364, ambas `highway=path`
- **Nodo inicial:** 2621350520
- **Nodo compartido:** 2150683165
- **Nodo final:** 9864044574
- **SHA-256 del acceso:** `449F2ABB13AE269FFA25772D7EB3F20F04CB7266FE8048AEC6961E3C453888ED`
- **SHA-256 del tramo principal:** `D18342C3E8FF511D9290A255439E5B180B82A7C74DB0F27E3F03B35F872568E3`
- **Uso posterior:** las dos vías se orientaron y unieron por su único nodo compartido; los originales se conservaron sin modificaciones

### URL de descarga del acceso

```text
https://api.openstreetmap.org/api/0.6/way/256471445/full
```

### URL de descarga del tramo principal

```text
https://api.openstreetmap.org/api/0.6/way/205097364/full
```

### Resultado provisional de R002

- **Geometría intermedia:** LineString válida, simple y continua
- **Distancia de ida:** 6.060 km
- **Distancia preliminar de ida y vuelta:** 12.119 km
- **Calidad preliminar:** dudosa; la longitud y el inicio son compatibles con Los Pantzas, pero las vías OSM no llevan ese nombre y la identidad exacta requiere confirmación

## R003 – Sendero Cascada Cóndor Machay

- **Fecha de descarga:** 2026-10-01
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Archivo obtenido:** `R003_condor_machay_osm_2026-10-01.osm`
- **Formato original:** OSM XML
- **Área descargada:** sector comprendido entre el Parqueadero Cascada Cóndor Machay y la cascada
- **Contenido del extracto:** 5.556 nodos y 182 vías
- **Segmentos utilizados:** 25 vías con etiqueta `highway=path`
- **Uso posterior:** los segmentos se filtraron y unieron en memoria; el archivo original no fue modificado

### URL de descarga

```text
https://api.openstreetmap.org/api/0.6/map?bbox=-78.435,-0.489,-78.419,-0.451
```

### Resultado de R003

- **Geometría intermedia:** LineString válida y continua
- **Distancia de ida:** 3.742 km
- **Distancia preliminar de ida y vuelta:** 7.484 km

## R005 – Sendero Tarabita - Cascada Nambillo

- **Fecha de descarga:** 2026-10-01
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Archivo obtenido:** `R005_nambillo_osm_2026-10-01.osm`
- **Formato original:** OSM XML
- **Contenido del extracto:** 1.114 nodos y 23 vías
- **Vías utilizadas:** 964152743 (Ruta 1) y 196510810 (Ruta 3)
- **Nodo compartido:** 2068378768
- **Punto de referencia:** nodo 5309163322, Cascada Nambillo
- **Uso posterior:** las dos vías se filtraron y unieron en memoria; el archivo original no fue modificado

### URL de descarga

```text
https://api.openstreetmap.org/api/0.6/map?bbox=-78.766,-0.082,-78.758,-0.076
```

### Resultado de R005

- **Geometría intermedia:** LineString válida y continua
- **Distancia de ida:** 0.951 km
- **Distancia preliminar de ida y vuelta:** 1.903 km
- **Separación mínima al punto OSM de la cascada:** 106.5 m
- **Calidad preliminar:** dudosa; el tramo final debe contrastarse con otra fuente

## R006 – Sendero al Ilaló

- **Fecha de descarga:** 2026-10-05
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Archivo obtenido:** `R006_ilalo_osm_2026-10-05.osm`
- **Formato original:** OSM XML
- **Contenido del extracto:** 2.346 nodos y 65 vías
- **Vía utilizada:** 198954451, `Sendero al Ilalo`
- **Nodos delimitadores:** 12867182981 (`Inicio del sendero`) y 12867182975 (`CIMA DEL SENDERO ILALO`)
- **Uso posterior:** se extrajo el subtramo de 36 nodos comprendido entre los dos puntos delimitadores; el archivo original no fue modificado

### URL de descarga

```text
https://api.openstreetmap.org/api/0.6/map?bbox=-78.431,-0.267,-78.415,-0.240
```

### Resultado de R006

- **Geometría intermedia:** LineString válida y continua
- **Distancia de ida:** 2.616 km
- **Distancia preliminar de ida y vuelta:** 5.232 km
- **Calidad preliminar:** apta para continuar con la incorporación de elevación

## R007 – Sendero sur al volcán El Corazón

- **Fecha de descarga:** 2026-10-06
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Archivo de la vía:** `R007_corazon_sur_osm_2026-10-06.osm`
- **Archivo del nodo de cumbre:** `R007_corazon_cumbre_osm_2026-10-06.osm`
- **Formato original:** OSM XML
- **Vía utilizada:** 356041538, `highway=path`
- **Nodo de inicio:** 2624530252
- **Extremo de la vía:** 3674114168
- **Nodo de cumbre:** 249409499, `Corazón`
- **Contenido del archivo de la vía:** 172 nodos y 1 vía
- **SHA-256 de la vía:** `D46BC003FD85CDB6E2FC42A15C029CFBA9E4CC8AD3BE584EF53679CA63AE5E9F`
- **SHA-256 de la cumbre:** `40719DC5E17D1EE5FDA576B1E6152ADFBE31875EC1065F09CD88D03117E2BE27`
- **Uso posterior:** los originales se conservaron sin modificar; el procesamiento agrega el nodo de cumbre al extremo de la vía porque la separación es de 2.088 m

### URL de descarga de la vía

```text
https://api.openstreetmap.org/api/0.6/way/356041538/full
```

### URL de descarga del nodo de cumbre

```text
https://api.openstreetmap.org/api/0.6/node/249409499
```

### Resultado de R007

- **Geometría intermedia:** LineString válida, simple y continua
- **Distancia de ida:** 3.838 km
- **Distancia preliminar de ida y vuelta:** 7.677 km
- **Calidad preliminar:** pendiente hasta procesar y revisar la elevación

## R004 – Circuito Pondoña (Sendero Pondoña)

- **Fecha de descarga:** 2026-10-06
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Archivo del conector:** `R004_pondona_conector_osm_2026-10-06.osm`
- **Archivo del circuito:** `R004_pondona_circuito_osm_2026-10-06.osm`
- **Archivo de la señal:** `R004_pondona_senal_osm_2026-10-06.osm`
- **Vías utilizadas:** `1057987723` y `1057987724`
- **Nodos compartidos:** `9721343634` y `9721343648`
- **Nodo guía:** `10025787156`, `Sendero Pondoña Trail`
- **SHA-256 del conector:** `80C4E6FEE07E8CE8A80EF0ACA9A4F47CA6B5112D5DD656E16921BB1F782A028E`
- **SHA-256 del circuito:** `A977DB9172DF23FB9B4C5561B6BEE02AB3BCB2A03F0EAF41D4208BD9BBF9E62F`
- **SHA-256 de la señal:** `6CDCF48EB1955AD56ED31A9B814F6F3FE6308800C764FA5E5382DFFDEFFCB452`
- **Uso posterior:** se extrajo de la primera vía únicamente el arco entre los nodos compartidos y se unió con la segunda vía; el ramal de acceso se excluyó para evitar duplicarlo en el circuito

### URL de descarga del conector

```text
https://api.openstreetmap.org/api/0.6/way/1057987723/full
```

### URL de descarga del circuito

```text
https://api.openstreetmap.org/api/0.6/way/1057987724/full
```

### URL de descarga de la señal

```text
https://api.openstreetmap.org/api/0.6/node/10025787156
```

### Resultado de R004

- **Geometría intermedia:** LineString cerrada, válida, simple y continua
- **Distancia total del circuito:** 1.663 km
- **Separación entre inicio y señal:** 14.337 m
- **Distancia indicada por la señal:** 2.000 km
- **Calidad preliminar:** apta para continuar hacia la clasificación física; la diferencia de longitud queda documentada

## Primer lote de ampliación R008–R010

- **Fecha de descarga:** 2026-10-07
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Procedimiento reproducible:** `06_scripts/descargar_lote_r008_r010.py`

| Ruta | Vía OSM | Nombre OSM | Archivo original | SHA-256 |
|---|---:|---|---|---|
| R008 | 1057988138 | Sendero al Pondoña | `R008_pondona_ascenso_osm_2026-10-07.osm` | `4E50877D128937F1AC8A8626233D421FBE9AC02BDE79D3AE43670EFC71B09AD1` |
| R009 | 1329296867 | Sendero Principal | `R009_maquipucuna_principal_osm_2026-10-07.osm` | `A25DF1590CA91E86532D4AFEF5879BCB1641B94F8987C4BC80FA3E6DCA9E8817` |
| R010 | 1329292949 | Sendero Tranquilo | `R010_maquipucuna_tranquilo_osm_2026-10-07.osm` | `0CCE6AB6DF39FFF76249CAA7E684B8458677CEB45F00633FCE508E12933EFFC8` |

Los archivos se conservaron sin modificaciones. Cada geometría intermedia se construyó a partir de la secuencia completa de nodos de su vía OSM mediante `06_scripts/procesar_lote_r008_r010.py`.

## Segundo lote de ampliación R011–R014

- **Fecha de descarga:** 2026-10-09
- **Destino:** Reserva Yanacocha, parroquia de Nono
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Procedimiento reproducible:** `06_scripts/descargar_lote_r011_r014.py`

| Ruta | Vía OSM | Nombre OSM | Archivo original | SHA-256 |
|---|---:|---|---|---|
| R011 | 470057044 | Masked Trogon | `R011_yanacocha_masked_trogon_osm_2026-10-09.osm` | `405CBE91C87DCFC0CE9B6731213870264ED3D7B04F809FEDA0A61C236A8DB268` |
| R012 | 470057046 | Andean Snipe Trail | `R012_yanacocha_andean_snipe_osm_2026-10-09.osm` | `AC67A6D9BE16010B28DA1D2D7257502D0E81B50C5DDA960D1268784ED1C99F3E` |
| R013 | 470057048 | Oso de Anteojos | `R013_yanacocha_oso_anteojos_osm_2026-10-09.osm` | `4A86803236351F29E82BE391712A154BE1043DB1F0CDE96E2C1125F17DF5C22A` |
| R014 | 723159928 | Trocha Inca | `R014_yanacocha_trocha_inca_osm_2026-10-09.osm` | `AF3499132AC01474E0B63A91205B63D857F59EB3105EA7E6B48E636030450AFB` |

Las cuatro vías son `highway=path`, poseen nombres diferenciados y se conservaron completas. La geometría y los extremos se pueden revisar conjuntamente en el mapa interactivo generado para Yanacocha.

## Tercer lote de ampliación R015–R017

- **Fecha de descarga:** 2026-10-09
- **Destino:** Mindo, cantón San Miguel de los Bancos
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Procedimiento reproducible:** `06_scripts/descargar_lote_r015_r017.py`

| Uso | Vía OSM | Nombre OSM | Archivo original | SHA-256 |
|---|---:|---|---|---|
| Acceso compartido R015–R016 | 1497391421 | Mindo Hermit Trail | `MINDO_hermit_acceso_osm_2026-10-09.osm` | `27DC2D73633D558DBE9ADFC5D33CB17240C416843293DC7B882A5A5715759639` |
| R015 | 1497391422 | Mindo Hermit Trail - Cascada Corazón | `R015_hermit_cascada_corazon_osm_2026-10-09.osm` | `26FB2DD2F3D4416A0D83F213A033A39DCE93A018AF356D10B21AE9B3FD4DF823` |
| R016 | 1497391425 | Mindo Hermit Trail - Mirador | `R016_hermit_mirador_osm_2026-10-09.osm` | `E2BB2734163880B87C951E1BC7CACA1BA239B99ED03744CBAB79EBA62F9E8B5F` |
| R017 | 299595681 | Yellow House Trail | `R017_yellow_house_trail_osm_2026-10-09.osm` | `4B7DE137541706B69F95BCF1C8EA22F58DAC687495209DC23379B98DEAEA5719` |

R015 y R016 comparten la vía de acceso `1497391421` y se separan en el nodo `13714085179`. El acceso compartido no se contabilizó como una ruta independiente. R017 utiliza una vía distinta y no comparte geometría con esas dos alternativas.

## Cuarto lote de ampliación R018

- **Fecha de descarga:** 2026-10-10
- **Destino:** Reserva Maquipucuna, parroquia de Nanegal
- **Fuente:** API oficial de OpenStreetMap
- **Licencia:** Open Database License (ODbL) 1.0
- **Procedimiento reproducible:** `06_scripts/descargar_r018.py`

| Ruta | Vía OSM | Nombre OSM | Archivo original | SHA-256 |
|---|---:|---|---|---|
| R018 | 801959483 | Sendero de la Cascada | `R018_maquipucuna_cascada_osm_2026-10-10.osm` | `0D6D78A73BB9C53B2DAF3A397EB17A440399B16726D20A03DFDDD4F78DC23C1B` |

La vía se conservó completa. Su longitud medida de 0.258 km por trayecto es compatible con la descripción documental de 0.200 km y retorno por el mismo sendero. Se descartaron como candidatas independientes las vías parciales de Humedal y Autoguiado porque no representan la extensión completa descrita para esos circuitos.

## Reutilización del original OSM para R019

- **Fecha de evaluación:** 2026-10-12; no hubo descarga nueva ni modificación del original.
- **Archivo fuente:** `R005_nambillo_osm_2026-10-01.osm`, descargado el 2026-10-01 desde la API OSM como se registra arriba.
- **SHA-256 del original compartido:** `6ED642B3EA7BBD358CC65C19627519B688ED5BA40A084ADF450068BA2C785BE3`.
- **Vía extraída:** 31543544, `Ruta 2`, `highway=footway`; licencia ODbL 1.0 y atribución OpenStreetMap.
- **Resultado:** `03_datos_intermedios/trazados/R019_trazado_ida_continuo_2026-10-12.geojson`; extracción reproducible con `06_scripts/procesar_r019.py`.

## Sexto lote: fuente original de R020 (geometría candidata)

- **Fecha de descarga:** 2026-10-14.
- **Vía OSM:** `299595680`, `Sendero 3`, `highway=footway`, `sac_scale=mountain_hiking`.
- **URL de descarga:** https://api.openstreetmap.org/api/0.6/way/299595680/full
- **Archivo original:** `R020_yellow_house_sendero3_osm_2026-10-14.osm`.
- **SHA-256:** `95853A03BC35A2DB2D56B98D7197C09761344AC662B600FE991C453889B2F66F`.
- **Licencia y atribución:** Open Database License (ODbL) 1.0; © OpenStreetMap contributors.
- **Procedimiento:** `06_scripts/descargar_r020_sendero3.py`. Se reutiliza sin modificar el original R017 para el acceso compartido. R020 no se cuenta como procesada ni elegible hasta completar el perfil y la auditoría.

## Séptimo lote: variante Yellow House por Senderos 1 y 2 (R021)

- **Consulta local:** 2026-10-17 (marca UTC de la base OSM: 2026-10-18T01:37:51Z).
- **Fuente:** [Overpass Turbo](https://overpass-turbo.eu/) / datos © OpenStreetMap contributors, ODbL 1.0.
- **Consulta reproducible:** `[out:json][timeout:90];way(id:299595681,301132246,301132249,301132250,301132251,1075614593,1075614594);out geom;`.
- **Original íntegro:** `Yellow_House_variantes_overpass_2026-10-17.json`, SHA-256 `57E1009D498EE7E7C4DADBB467B032B27C383A2E36DCF2D007ED323CFEEB2372`.
- **Vías usadas:** [Yellow House Trail 299595681](https://www.openstreetmap.org/way/299595681), [Sendero 1 301132246](https://www.openstreetmap.org/way/301132246), [Sendero 2 301132249](https://www.openstreetmap.org/way/301132249). Las vías adicionales del recorte se conservaron en el original, pero no se atribuyeron a R021.
- **Construcción:** `06_scripts/procesar_r021_yellow_house.py`; los dos desvíos reemplazan tramos de la línea principal entre pares de nodos OSM compartidos. No se interpolan uniones ni se inventa un destino.

El acceso actual, la autorización de ingreso y la independencia práctica de la variante frente a R017 siguen pendientes de comprobación. La elegibilidad es provisional; no debe presentarse como una nueva recomendación de visita.

## Octavo lote: instantánea normalizada de Cruz del Ilaló (R022)

- **Consulta local:** 2026-10-17; marca temporal Overpass UTC `2026-10-18T03:22:35Z`.
- **Consulta:** `[out:json][timeout:90];(way(id:272513972,297582904,198954451);node(4393010962););out geom;`.
- **Fuente:** [Overpass Turbo](https://overpass-turbo.eu/) sobre datos © OpenStreetMap contributors, ODbL 1.0.
- **Archivo archivado:** `R022_ilalo_cruz_overpass_snapshot_2026-10-17.json`, SHA-256 `6C1C1056DC33D3060116BC6B5F48628BF9B8314F2698C487DEB7B666B708FA32`.
- **Alcance real del archivo:** subconjunto normalizado que conserva la vía 297582904 completa (128 referencias y 128 coordenadas, etiquetas) y el nodo POI 4393010962. **No es una descarga byte a byte de la respuesta Overpass completa ni el XML oficial.** No contiene las otras vías consultadas.
- **Procesamiento:** `06_scripts/procesar_r022_ilalo.py` fija la huella y construye el trazado; el perfil DEM se deriva después.
- **Refuerzo realizado el 2026-10-20:** se archivó la respuesta XML exacta de `https://www.openstreetmap.org/api/0.6/way/297582904/full` en `R022_ilalo_cruz_osm_2026-10-20.osm` (25.946 bytes), SHA-256 `93C537C2B2386C74BCF4A8EAFE40A3A03984F4BE7AB92D10D147CA8620DD6381`. `06_scripts/contrastar_r022_xml_snapshot.py` verificó 128 referencias, coordenadas y etiquetas de vía contra el JSON, y el orden inverso del trazado procesado. Los nodos 9996501327 y 9996501328 tienen `ford=yes` en el XML; sus etiquetas no estaban en el JSON normalizado. El POI de la cruz procede del JSON, no de la respuesta `way/full`.
- **Pendiente:** verificar acceso público, transitabilidad y los dos posibles vados. El contraste geométrico no autoriza recomendar R022 a usuarios.

## Noveno lote: sendero a Cascada Guagrapamba (R023)

- **Fecha:** 2026-10-21. **Fuente:** respuesta XML de la API oficial OpenStreetMap para una caja pequeña alrededor de la cascada; URL y parámetros exactos reproducibles en `06_scripts/descargar_candidato_guagrapamba.py`.
- **Archivo original:** `candidato_guagrapamba_osm_2026-10-21.osm` (275020 bytes), SHA-256 `08223B3A9765EACF006A18DB9C7768A2C5ABE7F571F24EDFE1B11E12B746FD14`. Licencia de datos: Open Database License (ODbL) 1.0; atribución OpenStreetMap contributors.
- **Elementos empleados:** vía peatonal `1075564180` de 26 nodos; extremo final `8146768136` etiquetado como Cascada Guagrapamba; polígono de parqueadero `1205649963` solo como referencia de proximidad. No se usaron los otros caminos de la caja ni se añadió un conector inventado.
- **Control:** `06_scripts/procesar_r023_guagrapamba.py` comprueba la huella, etiquetas, orden, continuidad, longitud y extremo; `tests/test_procesar_r023_guagrapamba.py` y la auditoría integral comprueban el resultado. La mención municipal del destino se documenta en `01_documentacion/validacion_r023_guagrapamba_2026-10-21.md`.
- **Límite:** la nota municipal no prueba el acceso ni la transitabilidad en 2026. Uso provisional únicamente para análisis, sin recomendación a usuarios.

## Décimo lote: senderos al Mirador Cerro de la Luz (R024 y R025)

- **Fecha:** 2026-10-21. **Fuente:** respuesta XML de la API de mapa de OpenStreetMap (`bbox=-78.408,0.052,-78.395,0.060`), reproducible con `06_scripts/descargar_candidato_cerro_luz.py`.
- **Archivo original:** `candidato_cerro_luz_puellaro_osm_2026-10-21.osm` (223836 bytes), SHA-256 `B021608EFC1FAEEF530C2B96976472C3B607498A6FCC242BB56224CFE76652FB`. Licencia de datos: ODbL 1.0; atribución a OpenStreetMap contributors.
- **Elementos empleados:** vías `1209333234` (path), `1421205625` y `1421205624` (footway), nodo destino `11204680653`, vía de acceso `877695136` solo como referencia del inicio.
- **Control:** `06_scripts/procesar_r024_r025_cerro_luz.py`, `tests/test_procesar_cerro_luz.py` y la auditoría integral comprueban SHA-256, continuidad, extremos y diferenciación de las variantes.
- **Límite:** trazado creado en 2025 por un solo editor; acceso y permiso de ingreso por confirmar. Uso provisional únicamente para análisis, sin recomendación a usuarios. Detalle en `validacion_cerro_luz_puellaro_2026-10-21.md`.

## Undécimo lote: sendero Tarabita – Cascada Guarumos (R026)

- **Fecha:** 2026-10-22. **Fuente:** respuesta XML de la API de mapa de OpenStreetMap (`bbox=-78.768,-0.087,-78.757,-0.077`), reproducible con `06_scripts/descargar_candidato_guarumos.py`.
- **Archivo original:** `candidato_guarumos_colibries_mindo_osm_2026-10-22.osm` (213556 bytes), SHA-256 `09C8383A0DD356D9D33860C74E006FE637C0E976CA182B33C79927E35B61F0EC`. Licencia de datos: ODbL 1.0; atribución a OpenStreetMap contributors.
- **Elementos empleados:** vías `964152743` (Ruta 1), `196510810` (Ruta 3), `497709953` y `301136576` (footway); estación de la tarabita `352972925` (inicio) y nodo `3047618576` «Cascada Guarumos» (destino). La línea aérea `193975746` solo se usa para identificar la estación.
- **Control:** `06_scripts/procesar_r026_guarumos.py`, `tests/test_procesar_guarumos.py` y la auditoría integral comprueban SHA-256, continuidad, extremos y coincidencia con el camino mínimo por nodos compartidos.
- **Límite:** comparte casi todo el trazado con el preliminar de R005 (no elegible); cruzar la tarabita privada es previo al sendero (tarifa y horario de terceros por confirmar); sin mapa del operador. Detalle en `validacion_r026_guarumos_2026-10-22.md`.

## Duodécimo lote: Sendero del Viento, Moraspungo (R027)

- **Fecha:** 2026-10-22. **Fuente:** API de mapa de OpenStreetMap, `bbox=-78.507,0.018,-78.497,0.027`.
- **Archivo original:** `candidato_sendero_viento_moraspungo_osm_2026-10-22.osm` (190331 bytes), SHA-256 `F225BD3C26933E60B91CD56C9C1064A9C8EE5BB67BC54733C4E5FD5174DE7414`; ODbL 1.0, atribución OpenStreetMap contributors.
- **Elementos empleados:** vía peatonal adoquinada `724818033`, nodo inicial `347634309` compartido con vía de acceso `31263311`, nodo terminal `6797699199`. El mirador `6797709014` queda a 1,7 m pero no se conecta artificialmente.
- **Corroboración independiente:** [guía de turismo accesible](https://turismoaccesible.ec/site/destination/ecuador-accesible/region-sierra/pichincha/visita-al-crater-dormido/) describe el Sendero del Viento de unos 750 m y su destino recreativo en Moraspungo. Detalles y límites en `validacion_r027_sendero_viento_2026-10-22.md`.

## Enlaces generales

- Overpass Turbo: https://overpass-turbo.eu/
- API de OpenStreetMap: https://api.openstreetmap.org/
- Condiciones de uso y atribución: https://www.openstreetmap.org/copyright
