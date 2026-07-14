from datetime import datetime
from app.extensions import db
from app.constants import (
    VALOR_ACUMULADO_OFICIAL,
    VALOR_APUESTA_OFICIAL,
    VALOR_PREMIO_JORNADA_OFICIAL,
    VALOR_UTILIDAD_OFICIAL,
)
from app.utils.timezone import as_ecuador_naive, now_ecuador_naive


class JornadaGrupo(db.Model):
    __tablename__ = "jornadas_grupo"

    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupos.id"), nullable=False, index=True)
    numero_jornada = db.Column(db.Integer, nullable=False)

    nombre = db.Column(db.String(100), nullable=False)

    valor_apuesta = db.Column(db.Numeric(10, 2), nullable=False, default=VALOR_APUESTA_OFICIAL)
    valor_premio_jornada = db.Column(db.Numeric(10, 2), nullable=False, default=VALOR_PREMIO_JORNADA_OFICIAL)
    valor_acumulado = db.Column(db.Numeric(10, 2), nullable=False, default=VALOR_ACUMULADO_OFICIAL)
    valor_utilidad = db.Column(db.Numeric(10, 2), nullable=False, default=VALOR_UTILIDAD_OFICIAL)

    # NUEVOS CAMPOS
    total_jugadores_confirmados = db.Column(db.Integer, nullable=False, default=0)
    pozo_total = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    pozo_premio = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    pozo_acumulado = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    pozo_utilidad = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)

    ganador_apuesta_id = db.Column(db.Integer, db.ForeignKey("apuestas.id"), nullable=True)
    estado_ganador = db.Column(db.String(20), nullable=False, default="pendiente")
    # pendiente / definido / empatado

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

    grupo = db.relationship("Grupo", backref=db.backref("jornadas", lazy=True))

    ganador_apuesta = db.relationship(
        "Apuesta",
        foreign_keys=[ganador_apuesta_id],
        post_update=True
    )

    __table_args__ = (
        db.UniqueConstraint("grupo_id", "numero_jornada", name="uq_grupo_jornada"),
    )

    def estado_normalizado(self):
        return (self.estado or "").strip().lower()

    def estado_ganador_normalizado(self):
        return (self.estado_ganador or "").strip().lower()

    def esta_abierta_para_apuestas(self, ahora=None):
        ahora = as_ecuador_naive(ahora) or now_ecuador_naive()
        estado = self.estado_normalizado()
        if estado in {"cerrada", "liquidada"}:
            return False
        if not self.partidos:
            if estado != "abierta":
                return False
            fecha_cierre = as_ecuador_naive(self.fecha_cierre)
            if fecha_cierre and fecha_cierre <= ahora:
                return False
            return True
        return any(partido.acepta_pronosticos(ahora) for partido in self.partidos)

    def pronosticos_son_visibles(self):
        return not self.esta_abierta_para_apuestas()

    def estado_mostrable(self, ahora=None):
        estado = self.estado_normalizado()
        if self.esta_abierta_para_apuestas(ahora):
            return "Abierta"
        if estado == "liquidada":
            return "Liquidada"
        return "Cerrada"

    def __repr__(self):
        return f"<JornadaGrupo {self.nombre}>"
