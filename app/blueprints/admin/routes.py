from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.blueprints.admin import admin_bp
from app.models import JornadaGrupo, Usuario, PagoJornada, Partido, Apuesta, Pronostico
from app.extensions import db
from app.utils.puntos import calcular_puntos_pronostico
from datetime import datetime

from app.utils.pozo import (
    recalcular_pozo_jornada,
    detectar_ganador_jornada,
    mover_acumulado_jornada,
    jornada_completa_y_calculada,
)


def recalcular_ranking_jornada(jornada_id):
    apuestas = (
        Apuesta.query
        .filter_by(jornada_grupo_id=jornada_id)
        .order_by(Apuesta.puntos_total.desc(), Apuesta.id.asc())
        .all()
    )

    posicion = 1
    for apuesta in apuestas:
        apuesta.posicion = posicion
        posicion += 1

    db.session.commit()

def recalcular_puntos_partido(partido_id):
    partido = Partido.query.get(partido_id)
    if not partido:
        return

    if partido.goles_local is None or partido.goles_visitante is None:
        return

    pronosticos = Pronostico.query.filter_by(partido_id=partido.id).all()

    apuesta_ids_afectadas = set()

    for pronostico in pronosticos:
        puntos = calcular_puntos_pronostico(
            partido.goles_local,
            partido.goles_visitante,
            pronostico.goles_local_pred,
            pronostico.goles_visitante_pred
        )
        pronostico.puntos_obtenidos = puntos
        apuesta_ids_afectadas.add(pronostico.apuesta_id)

    db.session.flush()

    for apuesta_id in apuesta_ids_afectadas:
        apuesta = Apuesta.query.get(apuesta_id)
        if not apuesta:
            continue

        total = 0
        for p in apuesta.pronosticos:
            total += p.puntos_obtenidos

        apuesta.puntos_total = total

    db.session.commit()

    for apuesta_id in apuesta_ids_afectadas:
        apuesta = Apuesta.query.get(apuesta_id)
        if apuesta:
            recalcular_ranking_jornada(apuesta.jornada_grupo_id)

def admin_required():
    if not current_user.is_authenticated or not current_user.es_admin:
        abort(403)


@admin_bp.route("/")
def dashboard():
    return render_template("admin/dashboard.html")

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
def listar_jornadas():
    jornadas = (
        JornadaGrupo.query
        .order_by(JornadaGrupo.fecha_cierre.asc(), JornadaGrupo.id.asc())
        .all()
    )
    return render_template("admin/jornadas_listar.html", jornadas=jornadas)


@admin_bp.route("/jornadas/<int:jornada_id>")
def detalle_jornada(jornada_id):
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
        partidos=partidos
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

        pago = PagoJornada(
            usuario_id=usuario_id,
            jornada_grupo_id=jornada_id,
            valor=3.00,
            metodo_pago=metodo_pago,
            referencia=referencia,
            estado="pendiente",
            observacion=observacion
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
    pago.fecha_confirmacion = datetime.utcnow()
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

    return render_template("admin/partido_resultado.html", partido=partido)
