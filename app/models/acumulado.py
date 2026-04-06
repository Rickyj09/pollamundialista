from datetime import datetime
from app.extensions import db


class UsuarioAcumulado(db.Model):
    __tablename__ = "usuarios_acumulado"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    jornadas_validas_acumuladas = db.Column(db.Integer, nullable=False, default=0)
    monto_acumulado_aportado = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    habilitado_gran_final = db.Column(db.Boolean, nullable=False, default=False)
    fecha_habilitacion = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref("acumulado", uselist=False)
    )

    def __repr__(self):
        return f"<UsuarioAcumulado Usuario {self.usuario_id}>"

class PozoAcumulado(db.Model):
    __tablename__ = "pozos_acumulado"

    id = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(100), nullable=False, default="Gran Final Mundial")
    monto_actual = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)

    estado = db.Column(db.String(20), nullable=False, default="activo")
    # activo / cerrado / pagado

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self):
        return f"<PozoAcumulado {self.nombre}: {self.monto_actual}>"

class MovimientoAcumulado(db.Model):
    __tablename__ = "movimientos_acumulado"

    id = db.Column(db.Integer, primary_key=True)

    pozo_acumulado_id = db.Column(
        db.Integer,
        db.ForeignKey("pozos_acumulado.id"),
        nullable=False,
        index=True,
    )
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id"),
        nullable=True,
        index=True,
    )
    apuesta_id = db.Column(
        db.Integer,
        db.ForeignKey("apuestas.id"),
        nullable=True,
        index=True,
    )

    tipo = db.Column(db.String(30), nullable=False)
    # aporte / ajuste / premio_final

    valor = db.Column(db.Numeric(10, 2), nullable=False)
    detalle = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    pozo_acumulado = db.relationship(
        "PozoAcumulado",
        backref=db.backref("movimientos", lazy=True)
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref("movimientos_acumulado", lazy=True)
    )

    apuesta = db.relationship(
        "Apuesta",
        backref=db.backref("movimientos_acumulado", lazy=True)
    )

    def __repr__(self):
        return f"<MovimientoAcumulado {self.id} - {self.tipo} - {self.valor}>"