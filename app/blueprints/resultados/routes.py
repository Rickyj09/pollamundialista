from flask import render_template, request
from sqlalchemy.orm import selectinload, joinedload
from app.blueprints.resultados import resultados_bp
from app.models import JornadaGrupo, PozoAcumulado, Partido
from app.constants import (
    JORNADA_2_JORNADA_GRUPO_IDS,
    JORNADA_3_JORNADA_GRUPO_IDS,
    JORNADA_16AVOS_NOMBRE,
    JORNADA_8VOS_NOMBRE,
)
from app.utils.apuestas import apuesta_esta_pagada
from app.utils.ranking import (
    obtener_apuestas_ordenadas_jornada,
    obtener_ranking_general,
    obtener_ranking_por_jornadas,
)
from app.utils.apuestas import jornada_tiene_partidos_visibles


@resultados_bp.route("/")
def tabla():
    jornada_id = request.args.get("jornada_id", type=int)

    jornadas_cargadas = (
        JornadaGrupo.query
        .options(
            selectinload(JornadaGrupo.partidos).joinedload(Partido.equipo_local),
            selectinload(JornadaGrupo.partidos).joinedload(Partido.equipo_visitante),
            joinedload(JornadaGrupo.grupo),
        )
        .order_by(JornadaGrupo.fecha_cierre.asc(), JornadaGrupo.id.asc())
        .all()
    )
    jornadas = [
        jornada for jornada in jornadas_cargadas
        if jornada_tiene_partidos_visibles(jornada)
    ]

    apuestas = []
    jornada_seleccionada = None

    if jornada_id:
        jornada_seleccionada = JornadaGrupo.query.get(jornada_id)
        if jornada_seleccionada:
            apuestas = obtener_apuestas_ordenadas_jornada(jornada_id)

    return render_template(
        "resultados/tabla_v2.html",
        jornadas=jornadas,
        apuestas=apuestas,
        jornada_seleccionada=jornada_seleccionada
    )

@resultados_bp.route("/general")
def ranking_general():
    ranking = obtener_ranking_general()

    pozo_final = PozoAcumulado.query.filter_by(estado="activo").first()

    return render_template(
        "resultados/general_v2.html",
        ranking=ranking,
        pozo_final=pozo_final,
        ranking_title="Ranking general",
        ranking_description="Acumulado total por jugador, sumando puntos, exactos y aciertos de resultado de todas las jornadas.",
        ranking_scope_label="General acumulado",
        ranking_scope_ids=None,
    )


@resultados_bp.route("/jornada-2")
def ranking_jornada_2():
    ranking = obtener_ranking_por_jornadas(JORNADA_2_JORNADA_GRUPO_IDS)

    return render_template(
        "resultados/general_v2.html",
        ranking=ranking,
        pozo_final=None,
        ranking_title="Ranking Jornada 2",
        ranking_description="Ranking independiente de Jornada 2. Solo suma apuestas de los jornada_grupo_id 2, 5, 8, 11, 14 y 17.",
        ranking_scope_label="Jornada 2",
        ranking_scope_ids=JORNADA_2_JORNADA_GRUPO_IDS,
    )


@resultados_bp.route("/jornada-3")
def ranking_jornada_3():
    ranking = obtener_ranking_por_jornadas(JORNADA_3_JORNADA_GRUPO_IDS)

    return render_template(
        "resultados/general_v2.html",
        ranking=ranking,
        pozo_final=None,
        ranking_title="Ranking Jornada 3",
        ranking_description="Ranking independiente de Jornada 3. Solo suma apuestas de los jornada_grupo_id 3, 6, 9, 12, 15 y 18.",
        ranking_scope_label="Jornada 3",
        ranking_scope_ids=JORNADA_3_JORNADA_GRUPO_IDS,
    )


@resultados_bp.route("/16avos-de-final")
def ranking_16avos():
    jornada = JornadaGrupo.query.filter_by(nombre=JORNADA_16AVOS_NOMBRE).first()
    jornada_ids = (jornada.id,) if jornada else ()
    ranking = obtener_ranking_por_jornadas(jornada_ids)
    estados_pago_por_usuario = {}

    if jornada:
        for apuesta in obtener_apuestas_ordenadas_jornada(jornada.id):
            estados_pago_por_usuario[apuesta.usuario_id] = {
                "estado": (apuesta.estado_pago or "").strip().lower(),
                "pagada": apuesta_esta_pagada(apuesta.estado_pago),
            }

    return render_template(
        "resultados/general_v2.html",
        ranking=ranking,
        pozo_final=None,
        ranking_title="Ranking 16avos de final",
        ranking_description="Ranking independiente de 16avos de final. Solo suma la apuesta unica de esta fase.",
        ranking_scope_label="16avos de final",
        ranking_scope_ids=jornada_ids,
        mostrar_estado_pago=True,
        estados_pago_por_usuario=estados_pago_por_usuario,
    )


@resultados_bp.route("/8vos-de-final")
def ranking_8vos():
    jornada = JornadaGrupo.query.filter_by(nombre=JORNADA_8VOS_NOMBRE).first()
    jornada_ids = (jornada.id,) if jornada else ()
    ranking = obtener_ranking_por_jornadas(jornada_ids)
    estados_pago_por_usuario = {}

    if jornada:
        for apuesta in obtener_apuestas_ordenadas_jornada(jornada.id):
            estados_pago_por_usuario[apuesta.usuario_id] = {
                "estado": (apuesta.estado_pago or "").strip().lower(),
                "pagada": apuesta_esta_pagada(apuesta.estado_pago),
            }

    return render_template(
        "resultados/general_v2.html",
        ranking=ranking,
        pozo_final=None,
        ranking_title="Ranking 8vos de final",
        ranking_description="Ranking independiente de 8vos de final. Solo suma la apuesta unica de esta fase.",
        ranking_scope_label="8vos de final",
        ranking_scope_ids=jornada_ids,
        mostrar_estado_pago=True,
        estados_pago_por_usuario=estados_pago_por_usuario,
    )
