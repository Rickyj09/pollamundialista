"""agregar tercer puesto y final a semifinales

Revision ID: a7c8d9e0f1a2
Revises: f0b1c2d3e4f5
Create Date: 2026-07-15 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "a7c8d9e0f1a2"
down_revision = "f0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade():
    # La etapa final sigue siendo la misma JornadaGrupo SF/Semifinales.
    # Si la jornada fue liquidada tras los dos primeros partidos, se reabre
    # para permitir pronosticar los partidos 403 y 404 sin tocar apuestas.
    op.execute(
        """
        UPDATE jornadas_grupo
        SET
            fecha_cierre = '2026-07-19 13:59:00',
            estado_ganador = CASE
                WHEN LOWER(estado) IN ('cerrada', 'liquidada') THEN 'pendiente'
                ELSE estado_ganador
            END,
            ganador_apuesta_id = CASE
                WHEN LOWER(estado) IN ('cerrada', 'liquidada') THEN NULL
                ELSE ganador_apuesta_id
            END,
            estado = CASE
                WHEN LOWER(estado) IN ('cerrada', 'liquidada') THEN 'abierta'
                ELSE estado
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE numero_jornada = 1
          AND (
              nombre = 'Semifinales'
              OR grupo_id = (SELECT id FROM grupos WHERE nombre = 'SF' LIMIT 1)
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
            j.id,
            g.id,
            403,
            '2026-07-18',
            '16:00',
            '16:00',
            local.id,
            visitante.id,
            'Pendiente',
            'Pendiente',
            'pendiente',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM jornadas_grupo j
        JOIN grupos g ON g.id = j.grupo_id
        JOIN equipos local ON local.nombre = 'Francia'
        JOIN equipos visitante ON visitante.nombre = 'Inglaterra'
        WHERE g.nombre = 'SF'
          AND j.numero_jornada = 1
          AND NOT EXISTS (
              SELECT 1
              FROM partidos p
              WHERE p.jornada_grupo_id = j.id
                AND p.numero_calendario = 403
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
            j.id,
            g.id,
            404,
            '2026-07-19',
            '14:00',
            '14:00',
            local.id,
            visitante.id,
            'Pendiente',
            'Pendiente',
            'pendiente',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM jornadas_grupo j
        JOIN grupos g ON g.id = j.grupo_id
        JOIN equipos local ON local.id = (
            SELECT id
            FROM equipos
            WHERE nombre = 'Espana'
               OR nombre = 'Espa\u00f1a'
               OR nombre LIKE 'Espa%'
            ORDER BY id
            LIMIT 1
        )
        JOIN equipos visitante ON visitante.nombre = 'Argentina'
        WHERE g.nombre = 'SF'
          AND j.numero_jornada = 1
          AND NOT EXISTS (
              SELECT 1
              FROM partidos p
              WHERE p.jornada_grupo_id = j.id
                AND p.numero_calendario = 404
          )
        """
    )


def downgrade():
    op.execute(
        """
        DELETE FROM partidos
        WHERE numero_calendario IN (403, 404)
          AND jornada_grupo_id IN (
              SELECT j.id
              FROM jornadas_grupo j
              JOIN grupos g ON g.id = j.grupo_id
              WHERE g.nombre = 'SF'
                AND j.numero_jornada = 1
          )
          AND NOT EXISTS (
              SELECT 1
              FROM pronosticos pr
              WHERE pr.partido_id = partidos.id
          )
        """
    )
