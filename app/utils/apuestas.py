from collections import OrderedDict

from app.extensions import db
from app.models import Apuesta, PagoJornada, Pronostico
from app.constants import (
    EQUIPOS_SUDAMERICANOS_NORMALIZADOS,
    GRUPO_4TOS_NOMBRE,
    GRUPO_16AVOS_NOMBRE,
    GRUPO_8VOS_NOMBRE,
    JORNADA_4TOS_NOMBRE,
    JORNADA_16AVOS_NOMBRE,
    JORNADA_8VOS_NOMBRE,
)
from app.utils.timezone import now_ecuador_naive


FASES_ELIMINATORIAS_NOMBRES = {
    JORNADA_4TOS_NOMBRE.lower(): "4tos",
    JORNADA_16AVOS_NOMBRE.lower(): "16avos",
    JORNADA_8VOS_NOMBRE.lower(): "8vos",
}
FASES_ELIMINATORIAS_GRUPOS = {
    GRUPO_4TOS_NOMBRE.lower(): "4tos",
    GRUPO_16AVOS_NOMBRE.lower(): "16avos",
    GRUPO_8VOS_NOMBRE.lower(): "8vos",
}


def nombre_jornada_normalizado(jornada):
    if not jornada:
        return ""
    return ((jornada.nombre or "").strip().lower())


def nombre_grupo_jornada_normalizado(jornada):
    if not jornada or not getattr(jornada, "grupo", None):
        return ""
    return (((jornada.grupo.nombre if jornada.grupo else "") or "").strip().lower())


def jornada_es_16avos(jornada):
    if not jornada:
        return False
    return (
        nombre_jornada_normalizado(jornada) == JORNADA_16AVOS_NOMBRE.lower()
        or nombre_grupo_jornada_normalizado(jornada) == GRUPO_16AVOS_NOMBRE.lower()
    )


def jornada_es_4tos(jornada):
    if not jornada:
        return False
    return (
        nombre_jornada_normalizado(jornada) == JORNADA_4TOS_NOMBRE.lower()
        or nombre_grupo_jornada_normalizado(jornada) == GRUPO_4TOS_NOMBRE.lower()
    )


def jornada_es_8vos(jornada):
    if not jornada:
        return False
    return (
        nombre_jornada_normalizado(jornada) == JORNADA_8VOS_NOMBRE.lower()
        or nombre_grupo_jornada_normalizado(jornada) == GRUPO_8VOS_NOMBRE.lower()
    )


def jornada_es_fase_eliminatoria(jornada):
    if not jornada:
        return False
    return (
        nombre_jornada_normalizado(jornada) in FASES_ELIMINATORIAS_NOMBRES
        or nombre_grupo_jornada_normalizado(jornada) in FASES_ELIMINATORIAS_GRUPOS
    )


def slug_fase_eliminatoria(jornada):
    if not jornada:
        return None
    return (
        FASES_ELIMINATORIAS_NOMBRES.get(nombre_jornada_normalizado(jornada))
        or FASES_ELIMINATORIAS_GRUPOS.get(nombre_grupo_jornada_normalizado(jornada))
    )


def partido_incluye_equipo_sudamericano(partido):
    if not partido:
        return False

    nombres = [
        ((partido.equipo_local.nombre if partido.equipo_local else "") or "").strip().lower(),
        ((partido.equipo_visitante.nombre if partido.equipo_visitante else "") or "").strip().lower(),
    ]
    return any(nombre in EQUIPOS_SUDAMERICANOS_NORMALIZADOS for nombre in nombres)


def filtrar_partidos_sudamericanos(partidos):
    return [partido for partido in partidos if partido_incluye_equipo_sudamericano(partido)]


def obtener_partidos_visibles(jornada):
    partidos = list(jornada.partidos or [])
    if jornada_es_fase_eliminatoria(jornada):
        return partidos
    return filtrar_partidos_sudamericanos(partidos)


def jornada_tiene_partidos_visibles(jornada):
    return bool(obtener_partidos_visibles(jornada))


def jornada_esta_abierta(jornada, ahora=None):
    return jornada.esta_abierta_para_apuestas(ahora=ahora or now_ecuador_naive())


def usuario_tiene_pago_confirmado(usuario_id, jornada_id):
    pago = PagoJornada.query.filter_by(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada_id,
        estado="confirmado",
    ).first()
    return pago is not None


def estado_apuesta_normalizado(estado_pago):
    return ((estado_pago or "").strip().lower())


def apuesta_esta_pagada(estado_pago):
    return estado_apuesta_normalizado(estado_pago) in {"pagado", "confirmado"}


def obtener_partidos_ordenados(jornada):
    partidos_visibles = obtener_partidos_visibles(jornada)
    return sorted(
        partidos_visibles,
        key=lambda partido: (partido.fecha_partido, partido.numero_calendario or 0, partido.id),
    )


def obtener_apuesta_usuario_jornada(usuario_id, jornada_id):
    return Apuesta.query.filter_by(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada_id,
    ).first()


def agrupar_partidos_por_fecha(partidos):
    bloques = OrderedDict()

    for partido in partidos:
        fecha = partido.fecha_partido
        bloques.setdefault(fecha, []).append(partido)

    return [
        {
            "fecha": fecha,
            "partidos": partidos_fecha,
        }
        for fecha, partidos_fecha in bloques.items()
    ]


def obtener_estado_partidos(partidos, ahora=None):
    ahora = ahora or now_ecuador_naive()
    return {
        partido.id: {
            "ya_inicio": partido.ya_inicio(ahora),
            "inicio": partido.inicio_programado(),
        }
        for partido in partidos
    }


def construir_apuesta(
    usuario_id,
    jornada,
    metodo_pago="manual",
    referencia_pago=None,
    estado_pago="pagado",
    fecha_pago=None,
):
    return Apuesta(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada.id,
        valor_apostado=jornada.valor_apuesta,
        valor_premio_jornada=jornada.valor_premio_jornada,
        valor_aporte_acumulado=jornada.valor_acumulado,
        valor_utilidad=jornada.valor_utilidad,
        estado_pago=estado_pago,
        fecha_pago=fecha_pago if fecha_pago is not None else (now_ecuador_naive() if estado_pago in {"pagado", "confirmado"} else None),
        metodo_pago=metodo_pago,
        referencia_pago=referencia_pago,
        es_valida_para_acumulado=True,
    )


def construir_contexto_fase_eliminatoria(jornada, usuario_id, ahora=None):
    partidos = obtener_partidos_ordenados(jornada)
    apuesta = obtener_apuesta_usuario_jornada(usuario_id, jornada.id)
    pronosticos_dict = {
        pronostico.partido_id: pronostico
        for pronostico in (apuesta.pronosticos if apuesta else [])
    }
    estado_partidos = obtener_estado_partidos(partidos, ahora=ahora)

    return {
        "partidos": partidos,
        "bloques_por_fecha": agrupar_partidos_por_fecha(partidos),
        "apuesta": apuesta,
        "pronosticos_dict": pronosticos_dict,
        "estado_partidos": estado_partidos,
    }


def construir_contexto_16avos(jornada, usuario_id, ahora=None):
    return construir_contexto_fase_eliminatoria(jornada, usuario_id, ahora=ahora)


def leer_entero(form_data, key):
    if hasattr(form_data, "get"):
        try:
            return form_data.get(key, type=int)
        except TypeError:
            value = form_data.get(key)
    else:
        value = form_data[key] if key in form_data else None

    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def guardar_pronosticos_desde_form(apuesta, partidos, form_data, permitir_partidos_iniciados=False):
    pronosticos_dict = {pronostico.partido_id: pronostico for pronostico in apuesta.pronosticos}
    estado_partidos = obtener_estado_partidos(partidos)

    creados = 0
    actualizados = 0
    enviados = 0

    for partido in partidos:
        partido_bloqueado = estado_partidos[partido.id]["ya_inicio"] and not permitir_partidos_iniciados
        if partido_bloqueado:
            continue

        goles_local = leer_entero(form_data, f"goles_local_{partido.id}")
        goles_visitante = leer_entero(form_data, f"goles_visitante_{partido.id}")

        if goles_local is None and goles_visitante is None:
            continue

        enviados += 1

        if goles_local is None or goles_visitante is None:
            raise ValueError(
                "Debes ingresar ambos marcadores o dejar ambos campos vacios en cada partido habilitado."
            )
        if goles_local < 0 or goles_visitante < 0:
            raise ValueError("No se permiten marcadores negativos.")

        pronostico = pronosticos_dict.get(partido.id)
        if pronostico:
            pronostico.goles_local_pred = goles_local
            pronostico.goles_visitante_pred = goles_visitante
            pronostico.puntos_obtenidos = 0
            actualizados += 1
            continue

        db.session.add(
            Pronostico(
                apuesta_id=apuesta.id,
                partido_id=partido.id,
                goles_local_pred=goles_local,
                goles_visitante_pred=goles_visitante,
                puntos_obtenidos=0,
            )
        )
        creados += 1

    return {
        "creados": creados,
        "actualizados": actualizados,
        "enviados": enviados,
    }
