from datetime import datetime
from app.extensions import db


class Apuesta(db.Model):
    __tablename__ = "apuestas"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    jornada_grupo_id = db.Column(
        db.Integer,
        db.ForeignKey("jornadas_grupo.id"),
        nullable=False,
        index=True,
    )

    valor_apostado = db.Column(db.Numeric(10, 2), nullable=False, default=3.00)
    valor_premio_jornada = db.Column(db.Numeric(10, 2), nullable=False, default=2.00)
    valor_aporte_acumulado = db.Column(db.Numeric(10, 2), nullable=False, default=0.50)
    valor_utilidad = db.Column(db.Numeric(10, 2), nullable=False, default=0.50)

    estado_pago = db.Column(db.String(20), nullable=False, default="pendiente")
    # pendiente / pagado / anulado

    fecha_pago = db.Column(db.DateTime, nullable=True)
    metodo_pago = db.Column(db.String(50), nullable=True)
    referencia_pago = db.Column(db.String(100), nullable=True)

    puntos_total = db.Column(db.Integer, nullable=False, default=0)
    exactos = db.Column(db.Integer, nullable=False, default=0)
    aciertos_resultado = db.Column(db.Integer, nullable=False, default=0)
    posicion = db.Column(db.Integer, nullable=True)

    es_valida_para_acumulado = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref("apuestas", lazy=True)
    )

    jornada_grupo = db.relationship(
    "JornadaGrupo",
    backref="apuestas",
    foreign_keys=[jornada_grupo_id]
    )

    __table_args__ = (
        db.UniqueConstraint("usuario_id", "jornada_grupo_id", name="uq_usuario_jornada_apuesta"),
    )

    def __repr__(self):
        return f"<Apuesta {self.id} - Usuario {self.usuario_id} - Jornada {self.jornada_grupo_id}>"