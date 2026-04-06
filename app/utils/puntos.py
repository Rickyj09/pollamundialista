def tipo_resultado(goles_local, goles_visitante):
    if goles_local > goles_visitante:
        return "L"
    if goles_local < goles_visitante:
        return "V"
    return "E"


def calcular_puntos_pronostico(goles_local_real, goles_visitante_real, goles_local_pred, goles_visitante_pred):
    # exacto
    if goles_local_real == goles_local_pred and goles_visitante_real == goles_visitante_pred:
        return 3

    real = tipo_resultado(goles_local_real, goles_visitante_real)
    pred = tipo_resultado(goles_local_pred, goles_visitante_pred)

    if real == pred:
        return 1

    return 0