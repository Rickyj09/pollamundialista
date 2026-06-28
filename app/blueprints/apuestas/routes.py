from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.apuestas import apuestas_bp
from app.extensions import db
from app.models import JornadaGrupo, Apuesta, Usuario
from app.utils.apuestas import (
    construir_apuesta,
    guardar_pronosticos_desde_form,
    jornada_esta_abierta,
    jornada_es_16avos,
    obtener_estado_partidos,
    obtener_partidos_ordenados,
    usuario_tiene_pago_confirmado,
)


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
    partidos = obtener_partidos_ordenados(jornada)

    if not partidos:
        flash("Esta jornada no tiene partidos habilitados para la Polla Mundialista.", "warning")
        return redirect(url_for("jornadas.listar"))

    if not jornada_esta_abierta(jornada):
        flash("Esta jornada ya no tiene partidos disponibles para apostar.", "warning")
        return redirect(url_for("jornadas.listar"))

    if not usuario_tiene_pago_confirmado(current_user.id, jornada.id):
        flash("Tu pago para esta jornada aun no ha sido confirmado por el administrador.", "warning")
        return redirect(url_for("jornadas.listar"))

    return render_template(
        "apuestas/nueva_v2.html",
        jornada=jornada,
        partidos=partidos,
        estado_partidos=obtener_estado_partidos(partidos),
        usa_resultado_final_eliminatoria=jornada_es_16avos(jornada),
    )


@apuestas_bp.route("/guardar/<int:jornada_id>", methods=["POST"])
@login_required
def guardar_apuesta(jornada_id):
    jornada = JornadaGrupo.query.get_or_404(jornada_id)
    partidos = obtener_partidos_ordenados(jornada)

    if not partidos:
        flash("Esta jornada no tiene partidos habilitados para la Polla Mundialista.", "warning")
        return redirect(url_for("jornadas.listar"))

    if not jornada_esta_abierta(jornada):
        flash("La jornada ya no tiene partidos disponibles para apostar.", "danger")
        return redirect(url_for("jornadas.listar"))

    usuario_id = current_user.id
    if not usuario_id:
        flash("Debes seleccionar un usuario.", "danger")
        return redirect(url_for("apuestas.nueva_apuesta", jornada_id=jornada.id))

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        flash("Usuario no valido.", "danger")
        return redirect(url_for("apuestas.nueva_apuesta", jornada_id=jornada.id))

    apuesta_existente = Apuesta.query.filter_by(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada.id,
    ).first()

    if apuesta_existente:
        flash("Este usuario ya tiene una apuesta registrada para esta jornada.", "warning")
        return redirect(url_for("apuestas.editar_apuesta", apuesta_id=apuesta_existente.id))

    apuesta = construir_apuesta(usuario_id=usuario_id, jornada=jornada, metodo_pago="manual")

    db.session.add(apuesta)
    db.session.flush()

    try:
        guardar_pronosticos_desde_form(
            apuesta=apuesta,
            partidos=partidos,
            form_data=request.form,
            permitir_partidos_iniciados=False,
        )

        db.session.commit()
        flash("Apuesta registrada correctamente.", "success")
        return redirect(url_for("apuestas.mis_apuestas"))

    except ValueError as error:
        db.session.rollback()
        flash(str(error), "danger")
        return redirect(url_for("apuestas.nueva_apuesta", jornada_id=jornada.id))
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
    partidos = obtener_partidos_ordenados(jornada)

    if not partidos:
        flash("Esta jornada no tiene partidos habilitados para la Polla Mundialista.", "warning")
        return redirect(url_for("apuestas.mis_apuestas"))

    if not jornada_esta_abierta(jornada):
        flash("La apuesta ya no se puede editar porque todos los partidos editables de la jornada ya iniciaron.", "warning")
        return redirect(url_for("apuestas.mis_apuestas"))

    pronosticos_dict = {p.partido_id: p for p in apuesta.pronosticos}

    return render_template(
        "apuestas/editar_v2.html",
        apuesta=apuesta,
        jornada=jornada,
        partidos=partidos,
        pronosticos_dict=pronosticos_dict,
        estado_partidos=obtener_estado_partidos(partidos),
        usa_resultado_final_eliminatoria=jornada_es_16avos(jornada),
    )


@apuestas_bp.route("/actualizar/<int:apuesta_id>", methods=["POST"])
@login_required
def actualizar_apuesta(apuesta_id):
    apuesta = Apuesta.query.get_or_404(apuesta_id)

    if apuesta.usuario_id != current_user.id and not current_user.es_admin:
        flash("No tienes permiso para actualizar esta apuesta.", "danger")
        return redirect(url_for("apuestas.mis_apuestas"))

    jornada = apuesta.jornada_grupo
    partidos = obtener_partidos_ordenados(jornada)

    if not partidos:
        flash("Esta jornada no tiene partidos habilitados para la Polla Mundialista.", "warning")
        return redirect(url_for("apuestas.mis_apuestas"))

    if not jornada_esta_abierta(jornada):
        flash("La apuesta ya no se puede editar porque todos los partidos editables de la jornada ya iniciaron.", "danger")
        return redirect(url_for("apuestas.mis_apuestas"))

    try:
        guardar_pronosticos_desde_form(
            apuesta=apuesta,
            partidos=partidos,
            form_data=request.form,
            permitir_partidos_iniciados=False,
        )

        db.session.commit()
        flash("Apuesta actualizada correctamente.", "success")
        return redirect(url_for("apuestas.mis_apuestas"))

    except ValueError as error:
        db.session.rollback()
        flash(str(error), "warning")
        return redirect(url_for("apuestas.editar_apuesta", apuesta_id=apuesta.id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar la apuesta: {str(e)}", "danger")
        return redirect(url_for("apuestas.editar_apuesta", apuesta_id=apuesta.id))
