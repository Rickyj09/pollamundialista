from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.blueprints.admin import admin_bp
from app.models import (
    JornadaGrupo,
    Usuario,
    PagoJornada,
    Partido,
    Apuesta,
    Pronostico,
    AuditoriaApuestaAdmin,
)
from app.extensions import db
from app.constants import VALOR_APUESTA_OFICIAL

from app.utils.apuestas import (
    construir_apuesta,
    guardar_pronosticos_desde_form,
    jornada_esta_abierta,
    jornada_es_16avos,
    obtener_estado_partidos,
    obtener_partidos_ordenados,
    usuario_tiene_pago_confirmado,
)
from app.utils.pozo import (
    recalcular_pozo_jornada,
    detectar_ganador_jornada,
    mover_acumulado_jornada,
    jornada_completa_y_calculada,
)
from app.utils.ranking import (
    recalcular_apuesta,
    recalcular_ranking_general,
    recalcular_ranking_jornada,
)
from app.utils.timezone import now_ecuador_naive


def recalcular_puntos_partido(partido_id):
    partido = Partido.query.get(partido_id)
    if not partido:
        return

    pronosticos = Pronostico.query.filter_by(partido_id=partido.id).all()

    apuesta_ids_afectadas = set()

    for pronostico in pronosticos:
        apuesta_ids_afectadas.add(pronostico.apuesta_id)

    for apuesta_id in apuesta_ids_afectadas:
        recalcular_apuesta(apuesta_id)

    for apuesta_id in apuesta_ids_afectadas:
        apuesta = Apuesta.query.get(apuesta_id)
        if apuesta:
            recalcular_ranking_jornada(apuesta.jornada_grupo_id)

    db.session.commit()

def admin_required():
    if not current_user.is_authenticated or not current_user.es_admin:
        abort(403)


def registrar_auditoria_apuesta_admin(admin_usuario, beneficiario, jornada, apuesta, modo, motivo, detalle):
    db.session.add(
        AuditoriaApuestaAdmin(
            admin_usuario_id=admin_usuario.id,
            beneficiario_usuario_id=beneficiario.id,
            jornada_grupo_id=jornada.id,
            apuesta_id=apuesta.id if apuesta else None,
            modo=modo,
            motivo=motivo or None,
            detalle=detalle,
        )
    )


@admin_bp.route("/")
@login_required
def dashboard():
    admin_required()
    return render_template("admin/dashboard.html")


@admin_bp.route("/apuestas/registrar-por-usuario", methods=["GET", "POST"])
@login_required
def registrar_apuesta_por_usuario():
    admin_required()

    usuarios = (
        Usuario.query
        .filter_by(activo=True, es_admin=False)
        .order_by(Usuario.nombres.asc(), Usuario.apellidos.asc(), Usuario.id.asc())
        .all()
    )
    jornadas = (
        JornadaGrupo.query
        .order_by(JornadaGrupo.fecha_cierre.asc(), JornadaGrupo.id.asc())
        .all()
    )

    usuario_id = request.values.get("usuario_id", type=int)
    jornada_id = request.values.get("jornada_id", type=int)
    modo_registro = (request.values.get("modo_registro", "registro") or "registro").strip().lower()
    permitir_correccion = modo_registro == "correccion"
    motivo_valor = (request.values.get("motivo", "") or "").strip()

    usuario_seleccionado = Usuario.query.get(usuario_id) if usuario_id else None
    jornada_seleccionada = JornadaGrupo.query.get(jornada_id) if jornada_id else None
    apuesta_existente = None
    partidos = []
    estado_partidos = {}
    jornada_abierta = False

    if usuario_seleccionado and jornada_seleccionada:
        apuesta_existente = Apuesta.query.filter_by(
            usuario_id=usuario_seleccionado.id,
            jornada_grupo_id=jornada_seleccionada.id,
        ).first()
        partidos = obtener_partidos_ordenados(jornada_seleccionada)
        estado_partidos = obtener_estado_partidos(partidos)
        jornada_abierta = jornada_esta_abierta(jornada_seleccionada)

    if request.method == "POST":
        if not usuario_seleccionado or usuario_seleccionado.es_admin or not usuario_seleccionado.activo:
            flash("Debes seleccionar un participante valido.", "danger")
            return redirect(url_for("admin.registrar_apuesta_por_usuario"))

        if not jornada_seleccionada:
            flash("Debes seleccionar una jornada valida.", "danger")
            return redirect(url_for("admin.registrar_apuesta_por_usuario"))

        if not partidos:
            flash("La jornada seleccionada no tiene partidos habilitados para la Polla Mundialista.", "warning")
            return redirect(
                url_for(
                    "admin.registrar_apuesta_por_usuario",
                    usuario_id=usuario_seleccionado.id,
                    jornada_id=jornada_seleccionada.id,
                    modo_registro=modo_registro,
                )
            )

        if not jornada_abierta and not permitir_correccion:
            flash(
                "La jornada ya esta cerrada en hora Ecuador. Usa Correccion administrativa si necesitas dejar constancia excepcional.",
                "warning",
            )
            return redirect(
                url_for(
                    "admin.registrar_apuesta_por_usuario",
                    usuario_id=usuario_seleccionado.id,
                    jornada_id=jornada_seleccionada.id,
                    modo_registro=modo_registro,
                )
            )

        pago_confirmado = usuario_tiene_pago_confirmado(usuario_seleccionado.id, jornada_seleccionada.id)
        apuesta_pagada = apuesta_existente and (apuesta_existente.estado_pago or "").strip().lower() in {"pagado", "confirmado"}
        if not pago_confirmado and not apuesta_pagada:
            flash(
                "El participante necesita un pago confirmado para esta jornada antes de registrar la apuesta.",
                "warning",
            )
            return redirect(
                url_for(
                    "admin.registrar_apuesta_por_usuario",
                    usuario_id=usuario_seleccionado.id,
                    jornada_id=jornada_seleccionada.id,
                    modo_registro=modo_registro,
                )
            )

        try:
            apuesta = apuesta_existente
            creada_ahora = False
            if not apuesta:
                apuesta = construir_apuesta(
                    usuario_id=usuario_seleccionado.id,
                    jornada=jornada_seleccionada,
                    metodo_pago="admin",
                )
                db.session.add(apuesta)
                db.session.flush()
                creada_ahora = True

            resultado = guardar_pronosticos_desde_form(
                apuesta=apuesta,
                partidos=partidos,
                form_data=request.form,
                permitir_partidos_iniciados=permitir_correccion,
            )

            if resultado["enviados"] == 0:
                db.session.rollback()
                flash("Debes ingresar al menos un pronostico para guardar la apuesta administrativa.", "warning")
                return redirect(
                    url_for(
                        "admin.registrar_apuesta_por_usuario",
                        usuario_id=usuario_seleccionado.id,
                        jornada_id=jornada_seleccionada.id,
                        modo_registro=modo_registro,
                    )
                )

            recalcular_apuesta(apuesta.id)
            recalcular_ranking_jornada(jornada_seleccionada.id)
            detectar_ganador_jornada(jornada_seleccionada.id)

            registrar_auditoria_apuesta_admin(
                admin_usuario=current_user,
                beneficiario=usuario_seleccionado,
                jornada=jornada_seleccionada,
                apuesta=apuesta,
                modo=modo_registro,
                motivo=motivo_valor,
                detalle=(
                    f"creada={creada_ahora}; "
                    f"creados={resultado['creados']}; "
                    f"actualizados={resultado['actualizados']}; "
                    f"correccion={permitir_correccion}"
                ),
            )

            db.session.commit()
            flash("Apuesta administrativa guardada correctamente.", "success")
            return redirect(
                url_for(
                    "admin.registrar_apuesta_por_usuario",
                    usuario_id=usuario_seleccionado.id,
                    jornada_id=jornada_seleccionada.id,
                    modo_registro=modo_registro,
                )
            )
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "danger")
        except Exception as error:
            db.session.rollback()
            flash(f"No se pudo guardar la apuesta administrativa: {error}", "danger")

    return render_template(
        "admin/apuesta_por_usuario.html",
        usuarios=usuarios,
        jornadas=jornadas,
        usuario_seleccionado=usuario_seleccionado,
        jornada_seleccionada=jornada_seleccionada,
        apuesta_existente=apuesta_existente,
        pronosticos_dict={p.partido_id: p for p in apuesta_existente.pronosticos} if apuesta_existente else {},
        partidos=partidos,
        estado_partidos=estado_partidos,
        jornada_abierta=jornada_abierta,
        permitir_correccion=permitir_correccion,
        motivo_valor=motivo_valor,
    )


@admin_bp.route("/ranking/recalcular", methods=["POST"])
@login_required
def recalcular_rankings():
    admin_required()

    recalcular_ranking_general()

    jornadas = JornadaGrupo.query.order_by(JornadaGrupo.id.asc()).all()
    for jornada in jornadas:
        detectar_ganador_jornada(jornada.id)

    db.session.commit()

    flash("Ranking general, puntajes por jornada y desempates recalculados correctamente.", "success")
    return redirect(url_for("admin.dashboard"))

@admin_bp.route("/usuarios")
@login_required
def listar_usuarios():
    admin_required()
    usuarios = Usuario.query.order_by(Usuario.id.asc()).all()
    return render_template("admin/usuarios_listar.html", usuarios=usuarios)

@admin_bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_usuario():
    admin_required()

    if request.method == "POST":
        nombres = request.form.get("nombres", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        email = request.form.get("email", "").strip().lower()
        celular = request.form.get("celular", "").strip()
        password = request.form.get("password", "").strip()
        es_admin = True if request.form.get("es_admin") == "on" else False

        if not nombres or not email or not password:
            flash("Nombres, correo y contraseña son obligatorios.", "danger")
            return redirect(url_for("admin.nuevo_usuario"))

        existente = Usuario.query.filter_by(email=email).first()
        if existente:
            flash("Ya existe un usuario con ese correo.", "warning")
            return redirect(url_for("admin.nuevo_usuario"))

        usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            celular=celular,
            activo=True,
            es_admin=es_admin
        )
        usuario.set_password(password)

        db.session.add(usuario)
        db.session.commit()

        flash("Usuario creado correctamente.", "success")
        return redirect(url_for("admin.listar_usuarios"))

    return render_template("admin/usuarios_nuevo.html")


@admin_bp.route("/jornadas")
@login_required
def listar_jornadas():
    admin_required()
    jornadas = (
        JornadaGrupo.query
        .order_by(JornadaGrupo.fecha_cierre.asc(), JornadaGrupo.id.asc())
        .all()
    )
    return render_template("admin/jornadas_listar.html", jornadas=jornadas)


@admin_bp.route("/jornadas/<int:jornada_id>")
@login_required
def detalle_jornada(jornada_id):
    admin_required()
    jornada = JornadaGrupo.query.get(jornada_id)
    if not jornada:
        abort(404)

    partidos = sorted(
        jornada.partidos,
        key=lambda p: (p.fecha_partido, p.numero_calendario or 0)
    )

    return render_template(
        "admin/jornada_detalle.html",
        jornada=jornada,
        partidos=partidos,
        usa_resultado_final_eliminatoria=jornada_es_16avos(jornada),
    )

@admin_bp.route("/pagos")
@login_required
def listar_pagos():
    admin_required()
    pagos = PagoJornada.query.order_by(PagoJornada.id.desc()).all()
    return render_template("admin/pagos_listar.html", pagos=pagos)

@admin_bp.route("/pagos/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_pago():
    admin_required()

    usuarios = Usuario.query.filter_by(activo=True, es_admin=False).order_by(Usuario.nombres.asc()).all()
    jornadas = JornadaGrupo.query.order_by(JornadaGrupo.fecha_cierre.asc(), JornadaGrupo.id.asc()).all()

    if request.method == "POST":
        usuario_id = request.form.get("usuario_id", type=int)
        jornada_id = request.form.get("jornada_id", type=int)
        metodo_pago = request.form.get("metodo_pago", "").strip()
        referencia = request.form.get("referencia", "").strip()
        observacion = request.form.get("observacion", "").strip()

        existente = PagoJornada.query.filter_by(usuario_id=usuario_id, jornada_grupo_id=jornada_id).first()
        if existente:
            flash("Ya existe un registro de pago para ese usuario y jornada.", "warning")
            return redirect(url_for("admin.listar_pagos"))

        jornada = JornadaGrupo.query.get_or_404(jornada_id)

        pago = PagoJornada(
            usuario_id=usuario_id,
            jornada_grupo_id=jornada_id,
            valor=jornada.valor_apuesta or VALOR_APUESTA_OFICIAL,
            metodo_pago=metodo_pago,
            referencia=referencia,
            estado="pendiente",
            observacion=observacion,
            fecha_registro=now_ecuador_naive(),
        )

        db.session.add(pago)
        db.session.commit()

        flash("Pago registrado correctamente.", "success")
        return redirect(url_for("admin.listar_pagos"))

    return render_template("admin/pagos_nuevo.html", usuarios=usuarios, jornadas=jornadas)

@admin_bp.route("/pagos/<int:pago_id>/confirmar")
@login_required
def confirmar_pago(pago_id):
    admin_required()

    pago = PagoJornada.query.get_or_404(pago_id)
    pago.estado = "confirmado"
    pago.fecha_confirmacion = now_ecuador_naive()
    pago.confirmado_por_id = current_user.id

    db.session.flush()

    recalcular_pozo_jornada(pago.jornada_grupo_id)

    db.session.commit()

    flash("Pago confirmado y pozo recalculado correctamente.", "success")
    return redirect(url_for("admin.listar_pagos"))

@admin_bp.route("/partidos")
@login_required
def listar_partidos():
    admin_required()
    partidos = (
        Partido.query
        .order_by(Partido.fecha_partido.asc(), Partido.numero_calendario.asc())
        .all()
    )
    return render_template("admin/partidos_listar.html", partidos=partidos)


@admin_bp.route("/partidos/<int:partido_id>/resultado", methods=["GET", "POST"])
@login_required
def ingresar_resultado(partido_id):
    admin_required()
    partido = Partido.query.get_or_404(partido_id)

    if request.method == "POST":
        goles_local = request.form.get("goles_local", type=int)
        goles_visitante = request.form.get("goles_visitante", type=int)

        if goles_local is None or goles_visitante is None:
            flash("Debes ingresar ambos marcadores.", "danger")
            return redirect(url_for("admin.ingresar_resultado", partido_id=partido.id))
        if goles_local < 0 or goles_visitante < 0:
            flash("No se permiten marcadores negativos.", "danger")
            return redirect(url_for("admin.ingresar_resultado", partido_id=partido.id))

        partido.goles_local = goles_local
        partido.goles_visitante = goles_visitante
        partido.estado = "jugado"

        db.session.commit()

        recalcular_puntos_partido(partido.id)

        jornada = partido.jornada_grupo
        recalcular_pozo_jornada(jornada.id)

        if jornada_completa_y_calculada(jornada):
            detectar_ganador_jornada(jornada.id)
            mover_acumulado_jornada(jornada.id)
            jornada.estado = "liquidada"

        db.session.commit()

        flash("Resultado guardado, puntos recalculados y jornada actualizada.", "success")
        return redirect(url_for("admin.listar_partidos"))

    return render_template(
        "admin/partido_resultado.html",
        partido=partido,
        usa_resultado_final_eliminatoria=jornada_es_16avos(partido.jornada_grupo),
    )
