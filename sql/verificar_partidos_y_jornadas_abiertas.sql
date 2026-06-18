-- Verifica partidos abiertos/cerrados usando hora_est como referencia principal.
-- Si hora_est esta vacia, la app usa hora_local como respaldo.

SELECT
    p.id,
    p.jornada_grupo_id,
    j.nombre AS jornada,
    p.numero_calendario,
    p.fecha_partido,
    p.hora_est,
    p.hora_local,
    p.estado,
    CASE
        WHEN datetime(
            p.fecha_partido || ' ' || COALESCE(NULLIF(p.hora_est, ''), NULLIF(p.hora_local, ''))
        ) <= datetime('now', '-5 hours')
        THEN 'CERRADO'
        ELSE 'ABIERTO'
    END AS estado_pronostico
FROM partidos p
JOIN jornadas_grupo j ON j.id = p.jornada_grupo_id
ORDER BY p.fecha_partido, p.hora_est, p.numero_calendario;

-- Jornadas que todavia tienen al menos un partido editable.
SELECT
    j.id,
    j.nombre,
    j.estado,
    SUM(
        CASE
            WHEN datetime(
                p.fecha_partido || ' ' || COALESCE(NULLIF(p.hora_est, ''), NULLIF(p.hora_local, ''))
            ) > datetime('now', '-5 hours')
            THEN 1
            ELSE 0
        END
    ) AS partidos_editables
FROM jornadas_grupo j
JOIN partidos p ON p.jornada_grupo_id = j.id
GROUP BY j.id, j.nombre, j.estado
ORDER BY j.id;
