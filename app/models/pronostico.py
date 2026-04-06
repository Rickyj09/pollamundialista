from datetime import datetime
from app.extensions import db


class Pronostico(db.Model):
    __tablename__ = "pronosticos"

    id = db.Column(db.Integer, primary_key=True)

    apuesta_id = db.Column(
        db.Integer,
        db.ForeignKey("apuestas.id"),
        nullable=False,
        index=True,
    )
    partido_id = db.Column(
        db.Integer,
        db.ForeignKey("partidos.id"),
        nullable=False,
        index=True,
    )

    goles_local_pred = db.Column(db.Integer, nullable=False)
    goles_visitante_pred = db.Column(db.Integer, nullable=False)

    puntos_obtenidos = db.Column(db.Integer, nullable=False, default=0)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    apuesta = db.relationship(
        "Apuesta",
        backref=db.backref("pronosticos", lazy=True, cascade="all, delete-orphan")
    )

    partido = db.relationship(
        "Partido",
        backref=db.backref("pronosticos", lazy=True)
    )

    __table_args__ = (
        db.UniqueConstraint("apuesta_id", "partido_id", name="uq_apuesta_partido"),
    )

    def __repr__(self):
        return f"<Pronostico {self.id} - Apuesta {self.apuesta_id} - Partido {self.partido_id}>"