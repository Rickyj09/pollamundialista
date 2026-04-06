from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.blueprints.admin import admin_bp
from app.extensions import db
from app.models import JornadaGrupo, Usuario, PagoJornada
from datetime import datetime


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
    usuarios = Usuario.query.order_by(Usuario.nombres.asc()).all()
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
        .order_by(JornadaGrupo.grupo_id.asc(), JornadaGrupo.numero_jornada.asc())
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
    jornadas = JornadaGrupo.query.order_by(JornadaGrupo.grupo_id.asc(), JornadaGrupo.numero_jornada.asc()).all()

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

    db.session.commit()

    flash("Pago confirmado correctamente.", "success")
    return redirect(url_for("admin.listar_pagos"))