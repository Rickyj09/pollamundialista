from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.blueprints.apuestas import apuestas_bp
from app.extensions import db
from app.models import JornadaGrupo, Apuesta, Pronostico, Usuario, PagoJornada
from flask_login import current_user


def jornada_esta_abierta(jornada):
    if jornada.estado != "abierta":
        return False
    if jornada.fecha_cierre and datetime.utcnow() > jornada.fecha_cierre:
        return False
    return True


def usuario_puede_apostar(usuario_id, jornada_id):
    pago = PagoJornada.query.filter_by(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada_id,
        estado="confirmado"
    ).first()
    return pago is not None

@apuestas_bp.route("/")
@login_required
def mis_apuestas():
    apuestas = (
        Apuesta.query
        .filter_by(usuario_id=current_user.id)
        .order_by(Apuesta.id.desc())
        .all()
    )
    return render_template("apuestas/mis_apuestas.html", apuestas=apuestas)


@apuestas_bp.route("/nueva/<int:jornada_id>", methods=["GET"])
@login_required
def nueva_apuesta(jornada_id):
    jornada = JornadaGrupo.query.get_or_404(jornada_id)
    partidos = sorted(jornada.partidos, key=lambda p: (p.fecha_partido, p.numero_calendario or 0))

    if not jornada_esta_abierta(jornada):
        flash("Esta jornada no está disponible para apuestas.", "warning")
        return redirect(url_for("jornadas.listar"))

    if not usuario_puede_apostar(current_user.id, jornada.id):
        flash("Tu pago para esta jornada aún no ha sido confirmado por el administrador.", "warning")
        return redirect(url_for("jornadas.listar"))

    return render_template(
        "apuestas/nueva_v2.html",
        jornada=jornada,
        partidos=partidos
    )


@apuestas_bp.route("/guardar/<int:jornada_id>", methods=["POST"])
@login_required
def guardar_apuesta(jornada_id):
    jornada = JornadaGrupo.query.get_or_404(jornada_id)
    partidos = sorted(jornada.partidos, key=lambda p: (p.fecha_partido, p.numero_calendario or 0))

    if not jornada_esta_abierta(jornada):
        flash("La jornada ya no está abierta para apuestas.", "danger")
        return redirect(url_for("jornadas.listar"))

    usuario_id = current_user.id
    if not usuario_id:
        flash("Debes seleccionar un usuario.", "danger")
        return redirect(url_for("apuestas.nueva_apuesta", jornada_id=jornada.id))

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash("Usuario no válido.", "danger")
        return redirect(url_for("apuestas.nueva_apuesta", jornada_id=jornada.id))

    apuesta_existente = Apuesta.query.filter_by(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada.id
    ).first()

    if apuesta_existente:
        flash("Este usuario ya tiene una apuesta registrada para esta jornada.", "warning")
        return redirect(url_for("apuestas.editar_apuesta", apuesta_id=apuesta_existente.id))

    apuesta = Apuesta(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada.id,
        valor_apostado=jornada.valor_apuesta,
        valor_premio_jornada=jornada.valor_premio_jornada,
        valor_aporte_acumulado=jornada.valor_acumulado,
        valor_utilidad=jornada.valor_utilidad,
        estado_pago="pagado",
        fecha_pago=datetime.utcnow(),
        metodo_pago="manual",
        referencia_pago=None,
        es_valida_para_acumulado=True
    )

    db.session.add(apuesta)
    db.session.flush()

    try:
        for partido in partidos:
            goles_local_pred = request.form.get(f"goles_local_{partido.id}", type=int)
            goles_visitante_pred = request.form.get(f"goles_visitante_{partido.id}", type=int)

            if goles_local_pred is None or goles_visitante_pred is None:
                db.session.rollback()
                flash("Debes ingresar los marcadores de todos los partidos.", "danger")
                return redirect(url_for("apuestas.nueva_apuesta", jornada_id=jornada.id))

            pronostico = Pronostico(
                apuesta_id=apuesta.id,
                partido_id=partido.id,
                goles_local_pred=goles_local_pred,
                goles_visitante_pred=goles_visitante_pred,
                puntos_obtenidos=0
            )
            db.session.add(pronostico)

        db.session.commit()
        flash("Apuesta registrada correctamente.", "success")
        return redirect(url_for("apuestas.mis_apuestas"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error al guardar la apuesta: {str(e)}", "danger")
        return redirect(url_for("apuestas.nueva_apuesta", jornada_id=jornada.id))


@apuestas_bp.route("/editar/<int:apuesta_id>", methods=["GET"])
@login_required
def editar_apuesta(apuesta_id):
    apuesta = Apuesta.query.get_or_404(apuesta_id)

    if apuesta.usuario_id != current_user.id and not current_user.es_admin:
        flash("No tienes permiso para acceder a esta apuesta.", "danger")
        return redirect(url_for("apuestas.mis_apuestas"))

    jornada = apuesta.jornada_grupo
    partidos = sorted(jornada.partidos, key=lambda p: (p.fecha_partido, p.numero_calendario or 0))

    if not jornada_esta_abierta(jornada):
        flash("La apuesta ya no se puede editar porque la jornada está cerrada.", "warning")
        return redirect(url_for("apuestas.mis_apuestas"))

    pronosticos_dict = {p.partido_id: p for p in apuesta.pronosticos}

    return render_template(
        "apuestas/editar_v2.html",
        apuesta=apuesta,
        jornada=jornada,
        partidos=partidos,
        pronosticos_dict=pronosticos_dict
    )


@apuestas_bp.route("/actualizar/<int:apuesta_id>", methods=["POST"])
@login_required
def actualizar_apuesta(apuesta_id):
    apuesta = Apuesta.query.get_or_404(apuesta_id)

    # 🔒 Validar dueño o admin
    if apuesta.usuario_id != current_user.id and not current_user.es_admin:
        flash("No tienes permiso para actualizar esta apuesta.", "danger")
        return redirect(url_for("apuestas.mis_apuestas"))

    jornada = apuesta.jornada_grupo
    partidos = sorted(jornada.partidos, key=lambda p: (p.fecha_partido, p.numero_calendario or 0))

    # 🔒 Validar cierre de jornada
    if not jornada_esta_abierta(jornada):
        flash("La apuesta ya no se puede editar porque la jornada está cerrada.", "danger")
        return redirect(url_for("apuestas.mis_apuestas"))

    try:
        for pronostico in apuesta.pronosticos:
            goles_local = request.form.get(f"goles_local_{pronostico.partido_id}", type=int)
            goles_visitante = request.form.get(f"goles_visitante_{pronostico.partido_id}", type=int)

            if goles_local is None or goles_visitante is None:
                flash("Debes ingresar todos los marcadores.", "warning")
                return redirect(url_for("apuestas.editar_apuesta", apuesta_id=apuesta.id))

            pronostico.goles_local_pred = goles_local
            pronostico.goles_visitante_pred = goles_visitante

        db.session.commit()
        flash("Apuesta actualizada correctamente.", "success")
        return redirect(url_for("apuestas.mis_apuestas"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar la apuesta: {str(e)}", "danger")
        return redirect(url_for("apuestas.editar_apuesta", apuesta_id=apuesta.id))
