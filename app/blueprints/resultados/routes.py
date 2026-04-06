from flask import render_template
from app.blueprints.resultados import resultados_bp


@resultados_bp.route("/")
def tabla():
    return render_template("resultados/tabla.html")