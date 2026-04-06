from flask import render_template
from app.blueprints.jornadas import jornadas_bp
from app.models import JornadaGrupo


@jornadas_bp.route("/")
def listar():
    jornadas = (
        JornadaGrupo.query
        .order_by(JornadaGrupo.grupo_id.asc(), JornadaGrupo.numero_jornada.asc())
        .all()
    )
    return render_template("jornadas/listar.html", jornadas=jornadas)