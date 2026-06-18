from app.extensions import db
from app.models import Apuesta, PagoJornada, Pronostico
from app.constants import EQUIPOS_SUDAMERICANOS_NORMALIZADOS
from app.utils.timezone import now_ecuador_naive


def partido_incluye_equipo_sudamericano(partido):
    if not partido:
        return False

    nombres = [
        ((partido.equipo_local.nombre if partido.equipo_local else "") or "").strip().lower(),
        ((partido.equipo_visitante.nombre if partido.equipo_visitante else "") or "").strip().lower(),
    ]
    return any(nombre in EQUIPOS_SUDAMERICANOS_NORMALIZADOS for nombre in nombres)


def filtrar_partidos_sudamericanos(partidos):
    return [partido for partido in partidos if partido_incluye_equipo_sudamericano(partido)]


def jornada_esta_abierta(jornada, ahora=None):
    return jornada.esta_abierta_para_apuestas(ahora=ahora or now_ecuador_naive())


def usuario_tiene_pago_confirmado(usuario_id, jornada_id):
    pago = PagoJornada.query.filter_by(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada_id,
        estado="confirmado",
    ).first()
    return pago is not None


def obtener_partidos_ordenados(jornada):
    partidos_visibles = filtrar_partidos_sudamericanos(jornada.partidos)
    return sorted(
        partidos_visibles,
        key=lambda partido: (partido.fecha_partido, partido.numero_calendario or 0, partido.id),
    )


def obtener_estado_partidos(partidos, ahora=None):
    ahora = ahora or now_ecuador_naive()
    return {
        partido.id: {
            "ya_inicio": partido.ya_inicio(ahora),
            "inicio": partido.inicio_programado(),
        }
        for partido in partidos
    }


def construir_apuesta(usuario_id, jornada, metodo_pago="manual", referencia_pago=None):
    return Apuesta(
        usuario_id=usuario_id,
        jornada_grupo_id=jornada.id,
        valor_apostado=jornada.valor_apuesta,
        valor_premio_jornada=jornada.valor_premio_jornada,
        valor_aporte_acumulado=jornada.valor_acumulado,
        valor_utilidad=jornada.valor_utilidad,
        estado_pago="pagado",
        fecha_pago=now_ecuador_naive(),
        metodo_pago=metodo_pago,
        referencia_pago=referencia_pago,
        es_valida_para_acumulado=True,
    )


def leer_entero(form_data, key):
    if hasattr(form_data, "get"):
        try:
            return form_data.get(key, type=int)
        except TypeError:
            value = form_data.get(key)
    else:
        value = form_data[key] if key in form_data else None

    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def guardar_pronosticos_desde_form(apuesta, partidos, form_data, permitir_partidos_iniciados=False):
    pronosticos_dict = {pronostico.partido_id: pronostico for pronostico in apuesta.pronosticos}
    estado_partidos = obtener_estado_partidos(partidos)

    creados = 0
    actualizados = 0
    enviados = 0

    for partido in partidos:
        partido_bloqueado = estado_partidos[partido.id]["ya_inicio"] and not permitir_partidos_iniciados
        if partido_bloqueado:
            continue

        goles_local = leer_entero(form_data, f"goles_local_{partido.id}")
        goles_visitante = leer_entero(form_data, f"goles_visitante_{partido.id}")

        if goles_local is None and goles_visitante is None:
            continue

        enviados += 1

        if goles_local is None or goles_visitante is None:
            raise ValueError(
                "Debes ingresar ambos marcadores o dejar ambos campos vacios en cada partido habilitado."
            )

        pronostico = pronosticos_dict.get(partido.id)
        if pronostico:
            pronostico.goles_local_pred = goles_local
            pronostico.goles_visitante_pred = goles_visitante
            pronostico.puntos_obtenidos = 0
            actualizados += 1
            continue

        db.session.add(
            Pronostico(
                apuesta_id=apuesta.id,
                partido_id=partido.id,
                goles_local_pred=goles_local,
                goles_visitante_pred=goles_visitante,
                puntos_obtenidos=0,
            )
        )
        creados += 1

    return {
        "creados": creados,
        "actualizados": actualizados,
        "enviados": enviados,
    }
