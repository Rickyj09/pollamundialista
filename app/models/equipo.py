from datetime import datetime
from app.extensions import db


class Equipo(db.Model):
    __tablename__ = "equipos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True, index=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupos.id"), nullable=False, index=True)

    es_sudamericano = db.Column(db.Boolean, nullable=False, default=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    grupo = db.relationship(
        "Grupo",
        backref=db.backref("equipos", lazy=True)
    )

    def __repr__(self):
        return f"<Equipo {self.nombre}>"