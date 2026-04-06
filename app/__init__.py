from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager
from flask_login import current_user
from flask import redirect, url_for, request

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.before_request
    def requerir_login_global():
        rutas_publicas = [
            "auth.login",
            "static"
        ]

        if request.endpoint not in rutas_publicas and not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
    
    from app import models

    from app.blueprints.public import public_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.jornadas import jornadas_bp
    from app.blueprints.apuestas import apuestas_bp
    from app.blueprints.resultados import resultados_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(jornadas_bp, url_prefix="/jornadas")
    app.register_blueprint(apuestas_bp, url_prefix="/apuestas")
    app.register_blueprint(resultados_bp, url_prefix="/resultados")

    from app.seeds.seed_inicial import seed_inicial

    @app.cli.command("seed-inicial")
    def seed_inicial_command():
        seed_inicial()

    return app