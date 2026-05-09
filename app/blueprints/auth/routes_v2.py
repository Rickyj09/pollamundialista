from urllib.parse import urlparse

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.extensions import db
from app.models import Usuario


def obtener_redirect_destino():
    next_url = request.args.get("next") or request.form.get("next")
    if next_url and urlparse(next_url).netloc == "":
        return next_url
    return None


def redirect_auth(endpoint, next_url=None):
    if next_url:
        return redirect(url_for(endpoint, next=next_url))
    return redirect(url_for(endpoint))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.es_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("jornadas.listar"))

    next_url = obtener_redirect_destino()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.check_password(password):
            flash("Credenciales invalidas.", "danger")
            return redirect_auth("auth.login", next_url)

        if not usuario.activo:
            flash("Tu usuario esta inactivo.", "warning")
            return redirect_auth("auth.login", next_url)

        login_user(usuario)
        flash("Bienvenido al sistema.", "success")

        if next_url:
            return redirect(next_url)

        if usuario.es_admin:
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("jornadas.listar"))

    return render_template("auth/login_v2.html", next_url=next_url)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if current_user.es_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("jornadas.listar"))

    next_url = obtener_redirect_destino()

    if request.method == "POST":
        nombres = request.form.get("nombres", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not nombres:
            flash("Debes ingresar tu nombre.", "warning")
            return redirect_auth("auth.register", next_url)

        if not email:
            flash("Debes ingresar un correo electronico.", "warning")
            return redirect_auth("auth.register", next_url)

        if len(password) < 6:
            flash("La contrasena debe tener al menos 6 caracteres.", "warning")
            return redirect_auth("auth.register", next_url)

        if password != password_confirm:
            flash("La confirmacion de contrasena no coincide.", "warning")
            return redirect_auth("auth.register", next_url)

        existente = Usuario.query.filter_by(email=email).first()
        if existente:
            flash("Ya existe una cuenta registrada con ese correo.", "danger")
            return redirect_auth("auth.register", next_url)

        usuario = Usuario(
            nombres=nombres,
            apellidos=None,
            email=email,
            celular=None,
            activo=True,
            es_admin=False,
        )
        usuario.set_password(password)

        db.session.add(usuario)
        db.session.commit()

        login_user(usuario)
        flash("Tu cuenta fue creada correctamente.", "success")

        if next_url:
            return redirect(next_url)

        return redirect(url_for("jornadas.listar"))

    return render_template("auth/register_v2.html", next_url=next_url)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesion cerrada correctamente.", "success")
    return redirect(url_for("auth.login"))
