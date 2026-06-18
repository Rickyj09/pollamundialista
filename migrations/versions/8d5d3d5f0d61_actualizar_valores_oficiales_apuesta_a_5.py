"""actualizar valores oficiales de apuesta a 5

Revision ID: 8d5d3d5f0d61
Revises: dcf85988a74f
Create Date: 2026-06-09 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "8d5d3d5f0d61"
down_revision = "dcf85988a74f"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE jornadas_grupo
        SET valor_apuesta = 5.00,
            valor_premio_jornada = 4.00,
            valor_acumulado = 0.50,
            valor_utilidad = 0.50
        """
    )

    op.execute(
        """
        UPDATE pagos_jornada
        SET valor = 5.00
        """
    )

    op.execute(
        """
        UPDATE apuestas
        SET valor_apostado = 5.00,
            valor_premio_jornada = 4.00,
            valor_aporte_acumulado = 0.50,
            valor_utilidad = 0.50
        """
    )

    op.execute(
        """
        UPDATE jornadas_grupo
        SET total_jugadores_confirmados = (
                SELECT COUNT(*)
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            ),
            pozo_total = (
                SELECT COUNT(*) * jornadas_grupo.valor_apuesta
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            ),
            pozo_premio = (
                SELECT COUNT(*) * jornadas_grupo.valor_premio_jornada
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            ),
            pozo_acumulado = (
                SELECT COUNT(*) * jornadas_grupo.valor_acumulado
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            ),
            pozo_utilidad = (
                SELECT COUNT(*) * jornadas_grupo.valor_utilidad
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            )
        """
    )


def downgrade():
    op.execute(
        """
        UPDATE jornadas_grupo
        SET valor_apuesta = 3.00,
            valor_premio_jornada = 2.00,
            valor_acumulado = 0.50,
            valor_utilidad = 0.50
        """
    )

    op.execute(
        """
        UPDATE pagos_jornada
        SET valor = 3.00
        """
    )

    op.execute(
        """
        UPDATE apuestas
        SET valor_apostado = 3.00,
            valor_premio_jornada = 2.00,
            valor_aporte_acumulado = 0.50,
            valor_utilidad = 0.50
        """
    )

    op.execute(
        """
        UPDATE jornadas_grupo
        SET total_jugadores_confirmados = (
                SELECT COUNT(*)
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            ),
            pozo_total = (
                SELECT COUNT(*) * jornadas_grupo.valor_apuesta
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            ),
            pozo_premio = (
                SELECT COUNT(*) * jornadas_grupo.valor_premio_jornada
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            ),
            pozo_acumulado = (
                SELECT COUNT(*) * jornadas_grupo.valor_acumulado
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            ),
            pozo_utilidad = (
                SELECT COUNT(*) * jornadas_grupo.valor_utilidad
                FROM pagos_jornada
                WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
                  AND pagos_jornada.estado = 'confirmado'
            )
        """
    )
