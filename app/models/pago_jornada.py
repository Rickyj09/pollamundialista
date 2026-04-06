from datetime import datetime
from app.extensions import db


class PagoJornada(db.Model):
    __tablename__ = "pagos_jornada"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    jornada_grupo_id = db.Column(db.Integer, db.ForeignKey("jornadas_grupo.id"), nullable=False, index=True)

    valor = db.Column(db.Numeric(10, 2), nullable=False, default=3.00)
    metodo_pago = db.Column(db.String(50), nullable=True)
    referencia = db.Column(db.String(100), nullable=True)

    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    # pendiente / confirmado / rechazado

    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_confirmacion = db.Column(db.DateTime, nullable=True)

    confirmado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)

    observacion = db.Column(db.String(255), nullable=True)

    usuario = db.relationship(
        "Usuario",
        foreign_keys=[usuario_id],
        backref=db.backref("pagos_jornada", lazy=True)
    )

    confirmado_por = db.relationship(
        "Usuario",
        foreign_keys=[confirmado_por_id]
    )

    jornada_grupo = db.relationship(
        "JornadaGrupo",
        backref=db.backref("pagos_jornada", lazy=True)
    )

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        db.UniqueConstraint("usuario_id", "jornada_grupo_id", name="uq_pago_usuario_jornada"),
    )

    def __repr__(self):
        return f"<PagoJornada usuario={self.usuario_id} jornada={self.jornada_grupo_id} estado={self.estado}>"