from flask import render_template, request
from app.blueprints.resultados import resultados_bp
from app.models import JornadaGrupo, PozoAcumulado
from app.utils.ranking import obtener_apuestas_ordenadas_jornada, obtener_ranking_general


@resultados_bp.route("/")
def tabla():
    jornada_id = request.args.get("jornada_id", type=int)

    jornadas = (
        JornadaGrupo.query
        .order_by(JornadaGrupo.fecha_cierre.asc(), JornadaGrupo.id.asc())
        .all()
    )

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
        pozo_final=pozo_final
    )
