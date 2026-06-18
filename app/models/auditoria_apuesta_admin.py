from app.extensions import db
from app.utils.timezone import now_ecuador_naive


class AuditoriaApuestaAdmin(db.Model):
    __tablename__ = "auditoria_apuestas_admin"

    id = db.Column(db.Integer, primary_key=True)

    admin_usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    beneficiario_usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True)
    jornada_grupo_id = db.Column(db.Integer, db.ForeignKey("jornadas_grupo.id"), nullable=False, index=True)
    apuesta_id = db.Column(db.Integer, db.ForeignKey("apuestas.id"), nullable=True, index=True)

    modo = db.Column(db.String(30), nullable=False, default="registro")
    motivo = db.Column(db.String(255), nullable=True)
    detalle = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=now_ecuador_naive)

    admin_usuario = db.relationship(
        "Usuario",
        foreign_keys=[admin_usuario_id],
        backref=db.backref("auditorias_como_admin", lazy=True),
    )
    beneficiario_usuario = db.relationship(
        "Usuario",
        foreign_keys=[beneficiario_usuario_id],
        backref=db.backref("auditorias_como_beneficiario", lazy=True),
    )
    jornada_grupo = db.relationship(
        "JornadaGrupo",
        backref=db.backref("auditorias_apuestas_admin", lazy=True),
    )
    apuesta = db.relationship(
        "Apuesta",
        backref=db.backref("auditorias_admin", lazy=True),
    )

    def __repr__(self):
        return (
            f"<AuditoriaApuestaAdmin id={self.id} admin={self.admin_usuario_id} "
            f"beneficiario={self.beneficiario_usuario_id} jornada={self.jornada_grupo_id}>"
        )
