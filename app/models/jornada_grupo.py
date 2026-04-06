from datetime import datetime
from app.extensions import db


class JornadaGrupo(db.Model):
    __tablename__ = "jornadas_grupo"

    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupos.id"), nullable=False, index=True)
    numero_jornada = db.Column(db.Integer, nullable=False)  # 1, 2, 3

    nombre = db.Column(db.String(100), nullable=False)

    valor_apuesta = db.Column(db.Numeric(10, 2), nullable=False, default=3.00)
    valor_premio_jornada = db.Column(db.Numeric(10, 2), nullable=False, default=2.00)
    valor_acumulado = db.Column(db.Numeric(10, 2), nullable=False, default=0.50)
    valor_utilidad = db.Column(db.Numeric(10, 2), nullable=False, default=0.50)

    fecha_apertura = db.Column(db.DateTime, nullable=True)
    fecha_cierre = db.Column(db.DateTime, nullable=False)

    estado = db.Column(db.String(20), nullable=False, default="abierta")
    # abierta / cerrada / liquidada

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    grupo = db.relationship(
        "Grupo",
        backref=db.backref("jornadas", lazy=True)
    )

    __table_args__ = (
        db.UniqueConstraint("grupo_id", "numero_jornada", name="uq_grupo_jornada"),
    )

    def __repr__(self):
        return f"<JornadaGrupo {self.nombre}>"