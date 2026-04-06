from flask import render_template, request
from app.blueprints.resultados import resultados_bp
from app.models import JornadaGrupo, Apuesta
from sqlalchemy import func
from app.extensions import db
from app.models import Usuario

@resultados_bp.route("/")
def tabla():
    jornada_id = request.args.get("jornada_id", type=int)

    jornadas = (
        JornadaGrupo.query
        .order_by(JornadaGrupo.grupo_id.asc(), JornadaGrupo.numero_jornada.asc())
        .all()
    )

    apuestas = []
    jornada_seleccionada = None

    if jornada_id:
        jornada_seleccionada = JornadaGrupo.query.get(jornada_id)
        if jornada_seleccionada:
            apuestas = (
                Apuesta.query
                .filter_by(jornada_grupo_id=jornada_id)
                .order_by(Apuesta.puntos_total.desc(), Apuesta.posicion.asc(), Apuesta.id.asc())
                .all()
            )

    return render_template(
        "resultados/tabla.html",
        jornadas=jornadas,
        apuestas=apuestas,
        jornada_seleccionada=jornada_seleccionada
    )

@resultados_bp.route("/general")
def ranking_general():
    ranking = (
        db.session.query(
            Usuario.id,
            Usuario.nombres,
            Usuario.apellidos,
            func.coalesce(func.sum(Apuesta.puntos_total), 0).label("puntos")
        )
        .join(Apuesta, Apuesta.usuario_id == Usuario.id)
        .group_by(Usuario.id, Usuario.nombres, Usuario.apellidos)
        .order_by(func.sum(Apuesta.puntos_total).desc(), Usuario.nombres.asc())
        .all()
    )

    return render_template("resultados/general.html", ranking=ranking)