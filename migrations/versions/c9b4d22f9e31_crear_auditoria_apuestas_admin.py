"""crear auditoria de apuestas administradas

Revision ID: c9b4d22f9e31
Revises: 8d5d3d5f0d61
Create Date: 2026-06-18 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9b4d22f9e31"
down_revision = "8d5d3d5f0d61"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "auditoria_apuestas_admin",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("admin_usuario_id", sa.Integer(), nullable=False),
        sa.Column("beneficiario_usuario_id", sa.Integer(), nullable=False),
        sa.Column("jornada_grupo_id", sa.Integer(), nullable=False),
        sa.Column("apuesta_id", sa.Integer(), nullable=True),
        sa.Column("modo", sa.String(length=30), nullable=False),
        sa.Column("motivo", sa.String(length=255), nullable=True),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["admin_usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["apuesta_id"], ["apuestas.id"]),
        sa.ForeignKeyConstraint(["beneficiario_usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["jornada_grupo_id"], ["jornadas_grupo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_auditoria_apuestas_admin_admin_usuario_id"),
        "auditoria_apuestas_admin",
        ["admin_usuario_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditoria_apuestas_admin_apuesta_id"),
        "auditoria_apuestas_admin",
        ["apuesta_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditoria_apuestas_admin_beneficiario_usuario_id"),
        "auditoria_apuestas_admin",
        ["beneficiario_usuario_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auditoria_apuestas_admin_jornada_grupo_id"),
        "auditoria_apuestas_admin",
        ["jornada_grupo_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_auditoria_apuestas_admin_jornada_grupo_id"), table_name="auditoria_apuestas_admin")
    op.drop_index(op.f("ix_auditoria_apuestas_admin_beneficiario_usuario_id"), table_name="auditoria_apuestas_admin")
    op.drop_index(op.f("ix_auditoria_apuestas_admin_apuesta_id"), table_name="auditoria_apuestas_admin")
    op.drop_index(op.f("ix_auditoria_apuestas_admin_admin_usuario_id"), table_name="auditoria_apuestas_admin")
    op.drop_table("auditoria_apuestas_admin")
