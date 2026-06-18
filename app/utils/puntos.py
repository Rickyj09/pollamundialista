PUNTOS_RESULTADO_EXACTO = 5
PUNTOS_RESULTADO_CORRECTO = 3
ESTADOS_PARTIDO_CALCULABLES = {"jugado", "cerrado", "finalizado", "liquidado", "terminado"}


def tipo_resultado(goles_local, goles_visitante):
    if goles_local > goles_visitante:
        return "L"
    if goles_local < goles_visitante:
        return "V"
    return "E"


def partido_esta_calculable(partido):
    if not partido:
        return False
    if partido.goles_local is None or partido.goles_visitante is None:
        return False
    estado = (partido.estado or "").strip().lower()
    return estado in ESTADOS_PARTIDO_CALCULABLES


def calcular_puntos_pronostico(goles_local_real, goles_visitante_real, goles_local_pred, goles_visitante_pred):
    if goles_local_real == goles_local_pred and goles_visitante_real == goles_visitante_pred:
        return PUNTOS_RESULTADO_EXACTO

    real = tipo_resultado(goles_local_real, goles_visitante_real)
    pred = tipo_resultado(goles_local_pred, goles_visitante_pred)

    if real == pred:
        return PUNTOS_RESULTADO_CORRECTO

    return 0


def evaluar_pronostico(pronostico, partido):
    if not pronostico or not partido_esta_calculable(partido):
        return {
            "puntos": 0,
            "es_exacto": False,
            "acierto_resultado": False,
        }

    puntos = calcular_puntos_pronostico(
        partido.goles_local,
        partido.goles_visitante,
        pronostico.goles_local_pred,
        pronostico.goles_visitante_pred,
    )

    es_exacto = puntos == PUNTOS_RESULTADO_EXACTO
    acierto_resultado = puntos == PUNTOS_RESULTADO_CORRECTO

    return {
        "puntos": puntos,
        "es_exacto": es_exacto,
        "acierto_resultado": acierto_resultado,
    }
