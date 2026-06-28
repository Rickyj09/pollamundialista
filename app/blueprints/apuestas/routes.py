from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.blueprints.apuestas import apuestas_bp
from app.constants import JORNADA_16AVOS_NOMBRE
from app.extensions import db
from app.models import JornadaGrupo, Apuesta, Usuario
from app.utils.timezone import now_ecuador_naive
from app.utils.apuestas import (
    apuesta_esta_pagada,
    construir_contexto_16avos,
    construir_apuesta,
    estado_apuesta_normalizado,
    guardar_pronosticos_desde_form,
    obtener_apuesta_usuario_jornada,
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
    if jornada_es_16avos(jornada):
        return redirect(url_for("apuestas.listar_16avos"))

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
    if jornada_es_16avos(jornada):
        flash("En 16avos de final debes registrar cada pronostico partido por partido.", "warning")
        return redirect(url_for("apuestas.listar_16avos"))

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
    if jornada_es_16avos(jornada):
        return redirect(url_for("apuestas.listar_16avos"))

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
    if jornada_es_16avos(jornada):
        flash("En 16avos de final debes actualizar cada pronostico desde el partido correspondiente.", "warning")
        return redirect(url_for("apuestas.listar_16avos"))

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


def _obtener_jornada_16avos():
    jornada = JornadaGrupo.query.filter_by(nombre=JORNADA_16AVOS_NOMBRE).first_or_404()
    if not jornada_es_16avos(jornada):
        raise AssertionError("La jornada encontrada no corresponde a 16avos de final.")
    return jornada


@apuestas_bp.route("/16avos", methods=["GET"])
@login_required
def listar_16avos():
    jornada = _obtener_jornada_16avos()
    contexto = construir_contexto_16avos(jornada, current_user.id)
    pago_confirmado = usuario_tiene_pago_confirmado(current_user.id, jornada.id)
    estado_pago_apuesta = estado_apuesta_normalizado(contexto["apuesta"].estado_pago if contexto["apuesta"] else None)

    return render_template(
        "apuestas/16avos_lista.html",
        jornada=jornada,
        apuesta=contexto["apuesta"],
        bloques_por_fecha=contexto["bloques_por_fecha"],
        estado_partidos=contexto["estado_partidos"],
        pronosticos_dict=contexto["pronosticos_dict"],
        pago_confirmado=pago_confirmado,
        estado_pago_apuesta=estado_pago_apuesta,
        apuesta_pagada=apuesta_esta_pagada(estado_pago_apuesta),
    )


@apuestas_bp.route("/16avos/partido/<int:partido_id>", methods=["GET", "POST"])
@login_required
def pronosticar_partido_16avos(partido_id):
    jornada = _obtener_jornada_16avos()
    contexto = construir_contexto_16avos(jornada, current_user.id)
    partido = next((item for item in contexto["partidos"] if item.id == partido_id), None)

    if not partido:
        flash("El partido seleccionado no pertenece a 16avos de final.", "danger")
        return redirect(url_for("apuestas.listar_16avos"))

    apuesta = contexto["apuesta"]
    pronostico = contexto["pronosticos_dict"].get(partido.id)
    estado_partido = contexto["estado_partidos"].get(partido.id, {})
    partido_cerrado = bool(estado_partido.get("ya_inicio"))
    pago_confirmado = usuario_tiene_pago_confirmado(current_user.id, jornada.id)
    estado_pago_apuesta = estado_apuesta_normalizado(apuesta.estado_pago if apuesta else None)

    if request.method == "POST":
        if partido_cerrado:
            flash("Este partido ya inicio y no admite nuevos cambios.", "warning")
            return redirect(url_for("apuestas.pronosticar_partido_16avos", partido_id=partido.id))

        if apuesta is None:
            apuesta = construir_apuesta(
                usuario_id=current_user.id,
                jornada=jornada,
                metodo_pago="manual",
                estado_pago="pagado" if pago_confirmado else "pendiente",
                fecha_pago=now_ecuador_naive() if pago_confirmado else None,
            )
            db.session.add(apuesta)
            db.session.flush()

        try:
            resultado = guardar_pronosticos_desde_form(
                apuesta=apuesta,
                partidos=[partido],
                form_data=request.form,
                permitir_partidos_iniciados=False,
            )

            if resultado["enviados"] == 0:
                raise ValueError("Debes ingresar ambos marcadores para guardar este pronostico.")

            db.session.commit()
            flash("Pronostico guardado correctamente para 16avos de final.", "success")
            return redirect(url_for("apuestas.listar_16avos"))

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "danger")
        except Exception as error:
            db.session.rollback()
            flash(f"Error al guardar el pronostico: {error}", "danger")

        apuesta = obtener_apuesta_usuario_jornada(current_user.id, jornada.id)
        contexto = construir_contexto_16avos(jornada, current_user.id)
        pronostico = contexto["pronosticos_dict"].get(partido.id)
        estado_partido = contexto["estado_partidos"].get(partido.id, {})
        partido_cerrado = bool(estado_partido.get("ya_inicio"))
        estado_pago_apuesta = estado_apuesta_normalizado(apuesta.estado_pago if apuesta else None)

    return render_template(
        "apuestas/16avos_partido.html",
        jornada=jornada,
        partido=partido,
        apuesta=apuesta,
        pronostico=pronostico,
        partido_cerrado=partido_cerrado,
        pago_confirmado=pago_confirmado,
        estado_pago_apuesta=estado_pago_apuesta,
        apuesta_pagada=apuesta_esta_pagada(estado_pago_apuesta),
    )
