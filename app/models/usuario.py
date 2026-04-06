from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(120), nullable=False)
    apellidos = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(150), nullable=False, unique=True, index=True)
    celular = db.Column(db.String(30), nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)

    activo = db.Column(db.Boolean, nullable=False, default=True)
    es_admin = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def nombre_completo(self):
        if self.apellidos:
            return f"{self.nombres} {self.apellidos}"
        return self.nombres

    @property
    def is_active(self):
        return self.activo

    def __repr__(self):
        return f"<Usuario {self.id} - {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))