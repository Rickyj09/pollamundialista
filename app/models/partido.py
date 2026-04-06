from datetime import datetime
from app.extensions import db


class Partido(db.Model):
    __tablename__ = "partidos"

    id = db.Column(db.Integer, primary_key=True)

    jornada_grupo_id = db.Column(
        db.Integer,
        db.ForeignKey("jornadas_grupo.id"),
        nullable=False,
        index=True,
    )
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupos.id"), nullable=False, index=True)

    numero_calendario = db.Column(db.Integer, nullable=True)

    fecha_partido = db.Column(db.Date, nullable=False)
    hora_est = db.Column(db.String(10), nullable=True)
    hora_local = db.Column(db.String(10), nullable=True)

    equipo_local_id = db.Column(
        db.Integer,
        db.ForeignKey("equipos.id"),
        nullable=False,
        index=True,
    )
    equipo_visitante_id = db.Column(
        db.Integer,
        db.ForeignKey("equipos.id"),
        nullable=False,
        index=True,
    )

    estadio = db.Column(db.String(150), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)

    goles_local = db.Column(db.Integer, nullable=True)
    goles_visitante = db.Column(db.Integer, nullable=True)

    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    # pendiente / jugado / cerrado

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    jornada_grupo = db.relationship(
        "JornadaGrupo",
        backref=db.backref("partidos", lazy=True)
    )

    grupo = db.relationship(
        "Grupo",
        backref=db.backref("partidos", lazy=True)
    )

    equipo_local = db.relationship(
        "Equipo",
        foreign_keys=[equipo_local_id]
    )

    equipo_visitante = db.relationship(
        "Equipo",
        foreign_keys=[equipo_visitante_id]
    )

    def __repr__(self):
        return f"<Partido {self.id}: {self.equipo_local_id} vs {self.equipo_visitante_id}>"