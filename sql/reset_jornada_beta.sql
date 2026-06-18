-- Reinicia una jornada para pruebas beta sin borrar partidos.
-- Reemplaza :jornada_id por el id real de jornadas_grupo.

UPDATE jornadas_grupo
SET estado = 'abierta',
    estado_ganador = 'pendiente',
    ganador_apuesta_id = NULL,
    total_jugadores_confirmados = 0,
    pozo_total = 0,
    pozo_premio = 0,
    pozo_acumulado = 0,
    pozo_utilidad = 0
WHERE id = :jornada_id;

DELETE FROM pronosticos
WHERE apuesta_id IN (
    SELECT id
    FROM apuestas
    WHERE jornada_grupo_id = :jornada_id
);

DELETE FROM apuestas
WHERE jornada_grupo_id = :jornada_id;

DELETE FROM pagos_jornada
WHERE jornada_grupo_id = :jornada_id;
