from datetime import datetime
from app.extensions import db
from app.utils.timezone import ECUADOR_TIMEZONE, now_ecuador_naive


APP_TIMEZONE = ECUADOR_TIMEZONE


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

    def hora_referencia_apuestas(self):
        # Las horas cargadas se interpretan como hora oficial de Ecuador.
        return (self.hora_est or self.hora_local or "").strip() or None

    def inicio_programado(self):
        hora_referencia = self.hora_referencia_apuestas()
        if not self.fecha_partido or not hora_referencia:
            return None

        try:
            hora = datetime.strptime(hora_referencia, "%H:%M").time()
        except ValueError:
            return None

        return datetime.combine(self.fecha_partido, hora)

    def ya_inicio(self, ahora=None):
        ahora = ahora or now_ecuador_naive()
        inicio = self.inicio_programado()
        if inicio is None:
            return False
        return ahora >= inicio

    def __repr__(self):
        return f"<Partido {self.id}: {self.equipo_local_id} vs {self.equipo_visitante_id}>"
