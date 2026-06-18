from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import Apuesta, JornadaGrupo, Pronostico, Usuario
from app.utils.puntos import evaluar_pronostico


def recalcular_apuesta(apuesta_id):
    apuesta = (
        Apuesta.query
        .options(
            joinedload(Apuesta.usuario),
            joinedload(Apuesta.pronosticos).joinedload(Pronostico.partido),
        )
        .get(apuesta_id)
    )
    if not apuesta:
        return None

    puntos_total = 0
    exactos = 0
    aciertos_resultado = 0

    for pronostico in apuesta.pronosticos:
        detalle = evaluar_pronostico(pronostico, pronostico.partido)
        pronostico.puntos_obtenidos = detalle["puntos"]
        puntos_total += detalle["puntos"]
        exactos += int(detalle["es_exacto"])
        aciertos_resultado += int(detalle["acierto_resultado"])

    apuesta.puntos_total = puntos_total
    apuesta.exactos = exactos
    apuesta.aciertos_resultado = aciertos_resultado

    db.session.flush()
    return apuesta


def obtener_apuestas_ordenadas_jornada(jornada_id):
    return (
        Apuesta.query
        .join(Usuario, Usuario.id == Apuesta.usuario_id)
        .options(joinedload(Apuesta.usuario))
        .filter(Apuesta.jornada_grupo_id == jornada_id)
        .order_by(
            Apuesta.puntos_total.desc(),
            Apuesta.exactos.desc(),
            Apuesta.aciertos_resultado.desc(),
            Usuario.nombres.asc(),
            Usuario.apellidos.asc(),
            Apuesta.id.asc(),
        )
        .all()
    )


def recalcular_ranking_jornada(jornada_id):
    apuestas = obtener_apuestas_ordenadas_jornada(jornada_id)

    for posicion, apuesta in enumerate(apuestas, start=1):
        apuesta.posicion = posicion

    db.session.flush()
    return apuestas


def obtener_ranking_general():
    return (
        db.session.query(
            Usuario.id.label("usuario_id"),
            Usuario.nombres,
            Usuario.apellidos,
            func.coalesce(func.sum(Apuesta.puntos_total), 0).label("puntos"),
            func.coalesce(func.sum(Apuesta.exactos), 0).label("exactos"),
            func.coalesce(func.sum(Apuesta.aciertos_resultado), 0).label("aciertos_resultado"),
        )
        .outerjoin(Apuesta, Apuesta.usuario_id == Usuario.id)
        .filter(Usuario.es_admin.is_(False), Usuario.activo.is_(True))
        .group_by(Usuario.id, Usuario.nombres, Usuario.apellidos)
        .order_by(
            func.coalesce(func.sum(Apuesta.puntos_total), 0).desc(),
            func.coalesce(func.sum(Apuesta.exactos), 0).desc(),
            func.coalesce(func.sum(Apuesta.aciertos_resultado), 0).desc(),
            Usuario.nombres.asc(),
            Usuario.apellidos.asc(),
        )
        .all()
    )


def recalcular_ranking_general():
    jornada_ids = [
        jornada_id for (jornada_id,) in db.session.query(JornadaGrupo.id).order_by(JornadaGrupo.id.asc()).all()
    ]
    apuesta_ids = [
        apuesta_id for (apuesta_id,) in db.session.query(Apuesta.id).order_by(Apuesta.id.asc()).all()
    ]

    for apuesta_id in apuesta_ids:
        recalcular_apuesta(apuesta_id)

    for jornada_id in jornada_ids:
        recalcular_ranking_jornada(jornada_id)

    db.session.flush()
    return obtener_ranking_general()
