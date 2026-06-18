-- Actualiza el valor oficial de las jornadas existentes a USD 5.00.
-- Ajusta tambien el desglose financiero por jornada:
-- premio = 4.00, acumulado = 0.50, utilidad = 0.50.
-- Este proyecto usa la tabla jornadas_grupo y el campo numero_jornada.

UPDATE jornadas_grupo
SET valor_apuesta = 5.00,
    valor_premio_jornada = 4.00,
    valor_acumulado = 0.50,
    valor_utilidad = 0.50
WHERE numero_jornada IN (1, 2, 3);

UPDATE pagos_jornada
SET valor = 5.00
WHERE jornada_grupo_id IN (
    SELECT id
    FROM jornadas_grupo
    WHERE numero_jornada IN (1, 2, 3)
);

UPDATE apuestas
SET valor_apostado = 5.00,
    valor_premio_jornada = 4.00,
    valor_aporte_acumulado = 0.50,
    valor_utilidad = 0.50
WHERE jornada_grupo_id IN (
    SELECT id
    FROM jornadas_grupo
    WHERE numero_jornada IN (1, 2, 3)
);

UPDATE jornadas_grupo
SET total_jugadores_confirmados = (
        SELECT COUNT(*)
        FROM pagos_jornada
        WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
          AND pagos_jornada.estado = 'confirmado'
    ),
    pozo_total = (
        SELECT COUNT(*) * valor_apuesta
        FROM pagos_jornada
        WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
          AND pagos_jornada.estado = 'confirmado'
    ),
    pozo_premio = (
        SELECT COUNT(*) * valor_premio_jornada
        FROM pagos_jornada
        WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
          AND pagos_jornada.estado = 'confirmado'
    ),
    pozo_acumulado = (
        SELECT COUNT(*) * valor_acumulado
        FROM pagos_jornada
        WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
          AND pagos_jornada.estado = 'confirmado'
    ),
    pozo_utilidad = (
        SELECT COUNT(*) * valor_utilidad
        FROM pagos_jornada
        WHERE pagos_jornada.jornada_grupo_id = jornadas_grupo.id
          AND pagos_jornada.estado = 'confirmado'
    )
WHERE numero_jornada IN (1, 2, 3);
