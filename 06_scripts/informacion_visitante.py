"""Información de visita breve, separada de las reservas metodológicas del inventario.

Las fuentes describen el lugar o el servicio; ninguna entrada certifica apertura
en tiempo real ni convierte un trazado de OpenStreetMap en un sendero oficial.
"""

from __future__ import annotations

# resumen: tarjeta; detalle: ficha; fuente: página consultable por el visitante.
FICHAS = {
    "R001": {
        "resumen": "Alta montaña: revisa el terreno y la altitud.",
        "detalle": "Esta caminata llega a gran altitud e incluye un tramo T3 de montaña exigente por el arenal. El nivel de esfuerzo no describe la experiencia ni el cuidado que requiere ese terreno.",
    },
    "R006": {
        "resumen": "Consulta en el mapa el punto exacto de inicio.",
        "detalle": "El mapa marca el comienzo del tramo estudiado. El nombre del barrio de acceso no está respaldado por una fuente; utiliza el punto marcado y comprueba el acceso local antes de ir.",
    },
    "R011": {
        "resumen": "Mapa de un tramo de la Reserva Yanacocha.",
        "detalle": "La Reserva Yanacocha pertenece a la Fundación Jocotoco. El mapa representa el tramo digitalizado de este sendero; no tenemos un plano del administrador que permita afirmar que cubre toda la visita.",
        "fuente": "Fundación Jocotoco",
        "url": "https://www.jocotoco.org/es/nuestro-trabajo/nuestras-reservas/",
    },
    "R013": {
        "resumen": "Mapa de un tramo de la Reserva Yanacocha.",
        "detalle": "La Reserva Yanacocha pertenece a la Fundación Jocotoco. El mapa representa el tramo digitalizado de este sendero; no tenemos un plano del administrador que permita afirmar que cubre toda la visita.",
        "fuente": "Fundación Jocotoco",
        "url": "https://www.jocotoco.org/es/nuestro-trabajo/nuestras-reservas/",
    },
    "R020": {
        "resumen": "Senderos de una reserva privada en Mindo.",
        "detalle": "Yellow House / Hacienda San Vicente tiene un camino principal y senderos laterales señalizados. Esta opción usa el Sendero 3. Consulta las condiciones de ingreso en el establecimiento antes de ir.",
        "fuente": "Yellow House Trails & Lodge",
        "url": "https://www.ecuadormindobirds.com/",
    },
    "R021": {
        "resumen": "Senderos de una reserva privada en Mindo.",
        "detalle": "Yellow House / Hacienda San Vicente tiene un camino principal y senderos laterales señalizados. Esta opción combina los Senderos 1 y 2. Consulta en el establecimiento cuáles están abiertos al visitar.",
        "fuente": "Yellow House Trails & Lodge",
        "url": "https://www.ecuadormindobirds.com/",
    },
    "R022": {
        "resumen": "Hay posibles cruces de agua en el camino.",
        "detalle": "La ruta parte del sector Los Olivos hacia la Cruz del Ilaló. OpenStreetMap marca dos puntos del camino como posibles pasos de agua; revisa el estado del terreno antes de caminar.",
    },
    "R023": {
        "resumen": "Sendero hacia la Cascada Guagrapamba.",
        "detalle": "La caminata se dirige a la Cascada Guagrapamba, en la zona de Nono. Revisa en el punto de ingreso las condiciones del sendero antes de comenzar.",
        "fuente": "Visit Quito: Cascada de Guagrapamba",
        "url": "https://dev.visitquito.ec/travel/experience/cascada-de-guagrapamba/",
    },
    "R024": {
        "resumen": "Mirador comunitario de Puéllaro.",
        "detalle": "Este sendero lleva al Mirador Cerro de la Luz. El mirador es un atractivo turístico de Puéllaro; consulta localmente el acceso al sendero que muestra el mapa.",
        "fuente": "Quito Informa: Mirador Cerro La Luz",
        "url": "https://www.quitoinforma.gob.ec/2021/11/18/comunidad-de-puellaro-recibio-facilidades-y-senalizacion-turistica-en-el-cerro-la-luz/",
    },
    "R025": {
        "resumen": "Mirador comunitario de Puéllaro.",
        "detalle": "Esta alternativa más larga también termina en el Mirador Cerro de la Luz. El mirador es un atractivo turístico de Puéllaro; consulta localmente el acceso al sendero que muestra el mapa.",
        "fuente": "Quito Informa: Mirador Cerro La Luz",
        "url": "https://www.quitoinforma.gob.ec/2021/11/18/comunidad-de-puellaro-recibio-facilidades-y-senalizacion-turistica-en-el-cerro-la-luz/",
    },
    "R026": {
        "resumen": "Primero se cruza una tarabita de pago.",
        "detalle": "Para llegar al inicio de la caminata debes cruzar la tarabita del Santuario de Cascadas de Mindo. La distancia indicada corresponde al sendero desde la estación de desembarque hasta Guarumos y de regreso; no incluye el trayecto en tarabita. Consulta el precio y el horario del servicio antes de ir.",
        "fuente": "Tarabita y Santuario de Cascadas Mindo",
        "url": "https://mindo.info/es/actividades/tarabita-y-santuario-de-cascadas-mindo",
    },
    "R027": {
        "resumen": "Ingreso por el control de Moraspungo.",
        "detalle": "Para visitar este sector de la Reserva Geobotánica Pululahua debes registrarte en el puesto de control de Moraspungo y seguir la señalización de los senderos.",
        "fuente": "Ministerio del Ambiente: áreas protegidas de la Sierra",
        "url": "https://www.ambiente.gob.ec/wp-content/uploads/downloads/2024/11/Areas-Protegidas-Sierra-2.pdf",
    },
}


def ficha(id_ruta: str) -> dict[str, str]:
    return FICHAS.get(id_ruta, {})
