from decimal import Decimal
from app.models import PagoJornada, JornadaGrupo, PozoAcumulado, MovimientoAcumulado
from app.extensions import db
from app.utils.ranking import obtener_apuestas_ordenadas_jornada


def recalcular_pozo_jornada(jornada_id):
    jornada = JornadaGrupo.query.get(jornada_id)
    if not jornada:
        return

    pagos_confirmados = PagoJornada.query.filter_by(
        jornada_grupo_id=jornada.id,
        estado="confirmado"
    ).count()

    valor_apuesta = Decimal(str(jornada.valor_apuesta))
    valor_premio_unitario = Decimal(str(jornada.valor_premio_jornada))
    valor_acumulado_unitario = Decimal(str(jornada.valor_acumulado))
    valor_utilidad_unitaria = Decimal(str(jornada.valor_utilidad))

    jornada.total_jugadores_confirmados = pagos_confirmados
    jornada.pozo_total = pagos_confirmados * valor_apuesta
    jornada.pozo_premio = pagos_confirmados * valor_premio_unitario
    jornada.pozo_acumulado = pagos_confirmados * valor_acumulado_unitario
    jornada.pozo_utilidad = pagos_confirmados * valor_utilidad_unitaria

    db.session.flush()


def jornada_completa_y_calculada(jornada):
    if not jornada:
        return False

    if not jornada.partidos:
        return False

    for partido in jornada.partidos:
        if partido.goles_local is None or partido.goles_visitante is None:
            return False

    return True


def detectar_ganador_jornada(jornada_id):
    jornada = JornadaGrupo.query.get(jornada_id)
    if not jornada:
        return None

    apuestas = obtener_apuestas_ordenadas_jornada(jornada.id)

    if not apuestas:
        jornada.ganador_apuesta_id = None
        jornada.estado_ganador = "pendiente"
        db.session.flush()
        return None

    ganador = apuestas[0]
    llave_ganadora = (
        ganador.puntos_total,
        ganador.exactos,
        ganador.aciertos_resultado,
        (ganador.usuario.nombres or "").strip().lower(),
        (ganador.usuario.apellidos or "").strip().lower(),
    )
    empatados_totales = [
        apuesta
        for apuesta in apuestas
        if (
            apuesta.puntos_total,
            apuesta.exactos,
            apuesta.aciertos_resultado,
            (apuesta.usuario.nombres or "").strip().lower(),
            (apuesta.usuario.apellidos or "").strip().lower(),
        ) == llave_ganadora
    ]

    # Si incluso despues de los criterios oficiales hay empate absoluto,
    # la jornada queda marcada como empatada y no se asigna ganador unico.
    if len(empatados_totales) > 1:
        jornada.ganador_apuesta_id = None
        jornada.estado_ganador = "empatado"
        db.session.flush()
        return None

    jornada.ganador_apuesta_id = ganador.id
    jornada.estado_ganador = "definido"
    db.session.flush()
    return ganador


def obtener_pozo_final_activo():
    pozo = PozoAcumulado.query.filter_by(estado="activo").first()
    if not pozo:
        pozo = PozoAcumulado(
            nombre="Gran Final Mundial",
            monto_actual=Decimal("0.00"),
            estado="activo"
        )
        db.session.add(pozo)
        db.session.flush()
    return pozo


def mover_acumulado_jornada(jornada_id):
    jornada = JornadaGrupo.query.get(jornada_id)
    if not jornada:
        return

    pozo = obtener_pozo_final_activo()

    # evitar duplicados
    movimiento_existente = MovimientoAcumulado.query.filter_by(
        apuesta_id=None,
        detalle=f"Jornada {jornada.id} - {jornada.nombre}"
    ).first()

    if movimiento_existente:
        return

    monto = Decimal(str(jornada.pozo_acumulado or 0))
    if monto <= 0:
        return

    pozo.monto_actual = Decimal(str(pozo.monto_actual or 0)) + monto

    movimiento = MovimientoAcumulado(
        pozo_acumulado_id=pozo.id,
        usuario_id=None,
        apuesta_id=None,
        tipo="aporte",
        valor=monto,
        detalle=f"Jornada {jornada.id} - {jornada.nombre}"
    )
    db.session.add(movimiento)
    db.session.flush()
