"""agregar semifinales 2026

Revision ID: f0b1c2d3e4f5
Revises: c9b4d22f9e31
Create Date: 2026-07-14 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "f0b1c2d3e4f5"
down_revision = "c9b4d22f9e31"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        INSERT INTO grupos (nombre, descripcion, activo, created_at, updated_at)
        SELECT 'SF', 'Fase eliminatoria - semifinales', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        WHERE NOT EXISTS (SELECT 1 FROM grupos WHERE nombre = 'SF')
        """
    )

    for equipo in ("Francia", "Inglaterra", "Argentina"):
        op.execute(
            f"""
            INSERT INTO equipos (nombre, grupo_id, es_sudamericano, activo, created_at, updated_at)
            SELECT '{equipo}',
                   (SELECT id FROM grupos WHERE nombre = 'SF'),
                   {'1' if equipo == 'Argentina' else '0'},
                   1,
                   CURRENT_TIMESTAMP,
                   CURRENT_TIMESTAMP
            WHERE NOT EXISTS (SELECT 1 FROM equipos WHERE nombre = '{equipo}')
            """
        )

    op.execute(
        """
        INSERT INTO equipos (nombre, grupo_id, es_sudamericano, activo, created_at, updated_at)
        SELECT 'Espana',
               (SELECT id FROM grupos WHERE nombre = 'SF'),
               0,
               1,
               CURRENT_TIMESTAMP,
               CURRENT_TIMESTAMP
        WHERE NOT EXISTS (
            SELECT 1 FROM equipos
            WHERE nombre IN ('Espana', 'EspaÃ±a', 'Espa�a')
        )
        """
    )

    op.execute(
        """
        INSERT INTO jornadas_grupo (
            grupo_id,
            numero_jornada,
            nombre,
            valor_apuesta,
            valor_premio_jornada,
            valor_acumulado,
            valor_utilidad,
            total_jugadores_confirmados,
            pozo_total,
            pozo_premio,
            pozo_acumulado,
            pozo_utilidad,
            estado_ganador,
            fecha_apertura,
            fecha_cierre,
            estado,
            created_at,
            updated_at
        )
        SELECT
            (SELECT id FROM grupos WHERE nombre = 'SF'),
            1,
            'Semifinales',
            5.00,
            4.00,
            0.50,
            0.50,
            0,
            0.00,
            0.00,
            0.00,
            0.00,
            'pendiente',
            '2026-01-01 00:00:00',
            '2026-07-15 13:59:00',
            'abierta',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        WHERE NOT EXISTS (
            SELECT 1
            FROM jornadas_grupo
            WHERE grupo_id = (SELECT id FROM grupos WHERE nombre = 'SF')
              AND numero_jornada = 1
        )
        """
    )

    op.execute(
        """
        INSERT INTO partidos (
            jornada_grupo_id,
            grupo_id,
            numero_calendario,
            fecha_partido,
            hora_est,
            hora_local,
            equipo_local_id,
            equipo_visitante_id,
            estadio,
            ciudad,
            estado,
            created_at,
            updated_at
        )
        SELECT
            (SELECT id FROM jornadas_grupo WHERE grupo_id = (SELECT id FROM grupos WHERE nombre = 'SF') AND numero_jornada = 1),
            (SELECT id FROM grupos WHERE nombre = 'SF'),
            401,
            '2026-07-14',
            '14:00',
            '14:00',
            (SELECT id FROM equipos WHERE nombre = 'Francia'),
            (SELECT id FROM equipos WHERE nombre IN ('Espana', 'EspaÃ±a', 'Espa�a') ORDER BY id LIMIT 1),
            'Pendiente',
            'Pendiente',
            'pendiente',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        WHERE NOT EXISTS (
            SELECT 1
            FROM partidos
            WHERE jornada_grupo_id = (SELECT id FROM jornadas_grupo WHERE grupo_id = (SELECT id FROM grupos WHERE nombre = 'SF') AND numero_jornada = 1)
              AND numero_calendario = 401
        )
        """
    )

    op.execute(
        """
        INSERT INTO partidos (
            jornada_grupo_id,
            grupo_id,
            numero_calendario,
            fecha_partido,
            hora_est,
            hora_local,
            equipo_local_id,
            equipo_visitante_id,
            estadio,
            ciudad,
            estado,
            created_at,
            updated_at
        )
        SELECT
            (SELECT id FROM jornadas_grupo WHERE grupo_id = (SELECT id FROM grupos WHERE nombre = 'SF') AND numero_jornada = 1),
            (SELECT id FROM grupos WHERE nombre = 'SF'),
            402,
            '2026-07-15',
            '14:00',
            '14:00',
            (SELECT id FROM equipos WHERE nombre = 'Inglaterra'),
            (SELECT id FROM equipos WHERE nombre = 'Argentina'),
            'Pendiente',
            'Pendiente',
            'pendiente',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        WHERE NOT EXISTS (
            SELECT 1
            FROM partidos
            WHERE jornada_grupo_id = (SELECT id FROM jornadas_grupo WHERE grupo_id = (SELECT id FROM grupos WHERE nombre = 'SF') AND numero_jornada = 1)
              AND numero_calendario = 402
        )
        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM partidos
        WHERE jornada_grupo_id IN (
            SELECT id FROM jornadas_grupo
            WHERE grupo_id = (SELECT id FROM grupos WHERE nombre = 'SF')
        )
        AND numero_calendario IN (401, 402)
        AND NOT EXISTS (
            SELECT 1 FROM pronosticos WHERE pronosticos.partido_id = partidos.id
        )
        """
    )
    op.execute(
        """
        DELETE FROM jornadas_grupo
        WHERE grupo_id = (SELECT id FROM grupos WHERE nombre = 'SF')
          AND numero_jornada = 1
          AND NOT EXISTS (
              SELECT 1 FROM apuestas WHERE apuestas.jornada_grupo_id = jornadas_grupo.id
          )
          AND NOT EXISTS (
              SELECT 1 FROM partidos WHERE partidos.jornada_grupo_id = jornadas_grupo.id
          )
        """
    )
    op.execute(
        """
        DELETE FROM grupos
        WHERE nombre = 'SF'
          AND NOT EXISTS (SELECT 1 FROM jornadas_grupo WHERE jornadas_grupo.grupo_id = grupos.id)
          AND NOT EXISTS (SELECT 1 FROM equipos WHERE equipos.grupo_id = grupos.id)
        """
    )
