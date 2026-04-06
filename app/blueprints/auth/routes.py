from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.models import Usuario


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.check_password(password):
            flash("Credenciales inválidas.", "danger")
            return redirect(url_for("auth.login"))

        if not usuario.activo:
            flash("Tu usuario está inactivo.", "warning")
            return redirect(url_for("auth.login"))

        login_user(usuario)
        flash("Bienvenido al sistema.", "success")

        if usuario.es_admin:
            return redirect(url_for("admin.dashboard"))

        return redirect(url_for("jornadas.listar"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("auth.login"))