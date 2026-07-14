from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func, or_

from app.blueprints.apuestas import apuestas_bp
from app.constants import (
    GRUPO_4TOS_NOMBRE,
    GRUPO_16AVOS_NOMBRE,
    GRUPO_SEMIFINALES_NOMBRE,
    GRUPO_8VOS_NOMBRE,
    JORNADA_4TOS_NOMBRE,
    JORNADA_16AVOS_NOMBRE,
    JORNADA_SEMIFINALES_NOMBRE,
    JORNADA_8VOS_NOMBRE,
)
from app.extensions import db
from app.models import JornadaGrupo, Apuesta, Usuario, Grupo
from app.utils.timezone import now_ecuador_naive
from app.utils.apuestas import (
    apuesta_esta_pagada,
    construir_contexto_fase_eliminatoria,
    construir_apuesta,
    estado_apuesta_normalizado,
    guardar_pronosticos_desde_form,
    obtener_apuesta_usuario_jornada,
    jornada_esta_abierta,
    jornada_es_16avos,
    jornada_es_4tos,
    jornada_es_semifinales,
    jornada_es_8vos,
    jornada_es_fase_eliminatoria,
    obtener_estado_partidos,
    obtener_partidos_ordenados,
    slug_fase_eliminatoria,
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
    if jornada_es_fase_eliminatoria(jornada):
        return redirect(url_for(_endpoint_lista_fase_eliminatoria(jornada)))

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
        usa_resultado_final_eliminatoria=jornada_es_fase_eliminatoria(jornada),
    )


@apuestas_bp.route("/guardar/<int:jornada_id>", methods=["POST"])
@login_required
def guardar_apuesta(jornada_id):
    jornada = JornadaGrupo.query.get_or_404(jornada_id)
    if jornada_es_fase_eliminatoria(jornada):
        flash("En esta fase eliminatoria debes registrar cada pronostico partido por partido.", "warning")
        return redirect(url_for(_endpoint_lista_fase_eliminatoria(jornada)))

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
    if jornada_es_fase_eliminatoria(jornada):
        return redirect(url_for(_endpoint_lista_fase_eliminatoria(jornada)))

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
        usa_resultado_final_eliminatoria=jornada_es_fase_eliminatoria(jornada),
    )


@apuestas_bp.route("/actualizar/<int:apuesta_id>", methods=["POST"])
@login_required
def actualizar_apuesta(apuesta_id):
    apuesta = Apuesta.query.get_or_404(apuesta_id)

    if apuesta.usuario_id != current_user.id and not current_user.es_admin:
        flash("No tienes permiso para actualizar esta apuesta.", "danger")
        return redirect(url_for("apuestas.mis_apuestas"))

    jornada = apuesta.jornada_grupo
    if jornada_es_fase_eliminatoria(jornada):
        flash("En esta fase eliminatoria debes actualizar cada pronostico desde el partido correspondiente.", "warning")
        return redirect(url_for(_endpoint_lista_fase_eliminatoria(jornada)))

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
    jornada = (
        JornadaGrupo.query
        .join(Grupo, Grupo.id == JornadaGrupo.grupo_id)
        .filter(
            or_(
                func.lower(JornadaGrupo.nombre) == JORNADA_16AVOS_NOMBRE.lower(),
                func.lower(Grupo.nombre) == GRUPO_16AVOS_NOMBRE.lower(),
            )
        )
        .first()
    )
    if not jornada:
        jornada = JornadaGrupo.query.filter_by(nombre=JORNADA_16AVOS_NOMBRE).first_or_404()
    if not jornada_es_16avos(jornada):
        raise AssertionError("La jornada encontrada no corresponde a 16avos de final.")
    return jornada


def _obtener_jornada_4tos():
    jornada = (
        JornadaGrupo.query
        .join(Grupo, Grupo.id == JornadaGrupo.grupo_id)
        .filter(
            or_(
                func.lower(JornadaGrupo.nombre) == JORNADA_4TOS_NOMBRE.lower(),
                func.lower(Grupo.nombre) == GRUPO_4TOS_NOMBRE.lower(),
            )
        )
        .first()
    )
    if not jornada:
        jornada = JornadaGrupo.query.filter_by(nombre=JORNADA_4TOS_NOMBRE).first_or_404()
    if not jornada_es_4tos(jornada):
        raise AssertionError("La jornada encontrada no corresponde a 4tos de final.")
    return jornada


def _obtener_jornada_8vos():
    jornada = (
        JornadaGrupo.query
        .join(Grupo, Grupo.id == JornadaGrupo.grupo_id)
        .filter(
            or_(
                func.lower(JornadaGrupo.nombre) == JORNADA_8VOS_NOMBRE.lower(),
                func.lower(Grupo.nombre) == GRUPO_8VOS_NOMBRE.lower(),
            )
        )
        .first()
    )
    if not jornada:
        jornada = JornadaGrupo.query.filter_by(nombre=JORNADA_8VOS_NOMBRE).first_or_404()
    if not jornada_es_8vos(jornada):
        raise AssertionError("La jornada encontrada no corresponde a 8vos de final.")
    return jornada


def _obtener_jornada_semifinales():
    jornada = (
        JornadaGrupo.query
        .join(Grupo, Grupo.id == JornadaGrupo.grupo_id)
        .filter(
            or_(
                func.lower(JornadaGrupo.nombre) == JORNADA_SEMIFINALES_NOMBRE.lower(),
                func.lower(Grupo.nombre) == GRUPO_SEMIFINALES_NOMBRE.lower(),
            )
        )
        .first()
    )
    if not jornada:
        jornada = JornadaGrupo.query.filter_by(nombre=JORNADA_SEMIFINALES_NOMBRE).first_or_404()
    if not jornada_es_semifinales(jornada):
        raise AssertionError("La jornada encontrada no corresponde a semifinales.")
    return jornada


def _endpoint_lista_fase_eliminatoria(jornada):
    if jornada_es_4tos(jornada):
        return "apuestas.listar_4tos"
    if jornada_es_semifinales(jornada):
        return "apuestas.listar_semifinales"
    if jornada_es_16avos(jornada):
        return "apuestas.listar_16avos"
    if jornada_es_8vos(jornada):
        return "apuestas.listar_8vos"
    raise AssertionError("La jornada no corresponde a una fase eliminatoria soportada.")


def _endpoint_partido_fase_eliminatoria(jornada):
    if jornada_es_4tos(jornada):
        return "apuestas.pronosticar_partido_4tos"
    if jornada_es_semifinales(jornada):
        return "apuestas.pronosticar_partido_semifinales"
    if jornada_es_16avos(jornada):
        return "apuestas.pronosticar_partido_16avos"
    if jornada_es_8vos(jornada):
        return "apuestas.pronosticar_partido_8vos"
    raise AssertionError("La jornada no corresponde a una fase eliminatoria soportada.")


def _render_listado_fase_eliminatoria(jornada):
    contexto = construir_contexto_fase_eliminatoria(jornada, current_user.id)
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
        titulo_fase=jornada.nombre,
        endpoint_partido_fase=_endpoint_partido_fase_eliminatoria(jornada),
        url_lista_fase=url_for(_endpoint_lista_fase_eliminatoria(jornada)),
    )


def _render_partido_fase_eliminatoria(jornada, partido_id):
    contexto = construir_contexto_fase_eliminatoria(jornada, current_user.id)
    partido = next((item for item in contexto["partidos"] if item.id == partido_id), None)

    if not partido:
        flash("El partido seleccionado no pertenece a esta fase eliminatoria.", "danger")
        return redirect(url_for(_endpoint_lista_fase_eliminatoria(jornada)))

    apuesta = contexto["apuesta"]
    pronostico = contexto["pronosticos_dict"].get(partido.id)
    estado_partido = contexto["estado_partidos"].get(partido.id, {})
    partido_cerrado = not bool(estado_partido.get("acepta_pronosticos"))
    pago_confirmado = usuario_tiene_pago_confirmado(current_user.id, jornada.id)
    estado_pago_apuesta = estado_apuesta_normalizado(apuesta.estado_pago if apuesta else None)

    if request.method == "POST":
        if partido_cerrado:
            flash("Este partido ya está cerrado y no admite cambios en el pronóstico.", "warning")
            return redirect(url_for(_endpoint_lista_fase_eliminatoria(jornada)))

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
            flash(f"Pronostico guardado correctamente para {jornada.nombre}.", "success")
            return redirect(url_for(_endpoint_lista_fase_eliminatoria(jornada)))

        except ValueError as error:
            db.session.rollback()
            flash(str(error), "danger")
        except Exception as error:
            db.session.rollback()
            flash(f"Error al guardar el pronostico: {error}", "danger")

        apuesta = obtener_apuesta_usuario_jornada(current_user.id, jornada.id)
        contexto = construir_contexto_fase_eliminatoria(jornada, current_user.id)
        pronostico = contexto["pronosticos_dict"].get(partido.id)
        estado_partido = contexto["estado_partidos"].get(partido.id, {})
        partido_cerrado = not bool(estado_partido.get("acepta_pronosticos"))
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
        titulo_fase=jornada.nombre,
        url_lista_fase=url_for(_endpoint_lista_fase_eliminatoria(jornada)),
        endpoint_partido_fase=_endpoint_partido_fase_eliminatoria(jornada),
        slug_fase=slug_fase_eliminatoria(jornada),
    )


@apuestas_bp.route("/16avos", methods=["GET"])
@login_required
def listar_16avos():
    jornada = _obtener_jornada_16avos()
    return _render_listado_fase_eliminatoria(jornada)


@apuestas_bp.route("/4tos", methods=["GET"])
@login_required
def listar_4tos():
    jornada = _obtener_jornada_4tos()
    return _render_listado_fase_eliminatoria(jornada)


@apuestas_bp.route("/8vos", methods=["GET"])
@login_required
def listar_8vos():
    jornada = _obtener_jornada_8vos()
    return _render_listado_fase_eliminatoria(jornada)


@apuestas_bp.route("/semifinales", methods=["GET"])
@login_required
def listar_semifinales():
    jornada = _obtener_jornada_semifinales()
    return _render_listado_fase_eliminatoria(jornada)


@apuestas_bp.route("/16avos/partido/<int:partido_id>", methods=["GET", "POST"])
@login_required
def pronosticar_partido_16avos(partido_id):
    jornada = _obtener_jornada_16avos()
    return _render_partido_fase_eliminatoria(jornada, partido_id)


@apuestas_bp.route("/4tos/partido/<int:partido_id>", methods=["GET", "POST"])
@login_required
def pronosticar_partido_4tos(partido_id):
    jornada = _obtener_jornada_4tos()
    return _render_partido_fase_eliminatoria(jornada, partido_id)


@apuestas_bp.route("/8vos/partido/<int:partido_id>", methods=["GET", "POST"])
@login_required
def pronosticar_partido_8vos(partido_id):
    jornada = _obtener_jornada_8vos()
    return _render_partido_fase_eliminatoria(jornada, partido_id)


@apuestas_bp.route("/semifinales/partido/<int:partido_id>", methods=["GET", "POST"])
@login_required
def pronosticar_partido_semifinales(partido_id):
    jornada = _obtener_jornada_semifinales()
    return _render_partido_fase_eliminatoria(jornada, partido_id)
