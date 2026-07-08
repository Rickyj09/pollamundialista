from decimal import Decimal

EQUIPOS_SUDAMERICANOS = (
    "Argentina",
    "Brasil",
    "Colombia",
    "Ecuador",
    "Paraguay",
    "Uruguay",
)

EQUIPOS_SUDAMERICANOS_NORMALIZADOS = {nombre.strip().lower() for nombre in EQUIPOS_SUDAMERICANOS}
JORNADA_2_JORNADA_GRUPO_IDS = (2, 5, 8, 11, 14, 17)
JORNADA_3_JORNADA_GRUPO_IDS = (3, 6, 9, 12, 15, 18)
GRUPO_4TOS_NOMBRE = "4F"
JORNADA_4TOS_NOMBRE = "4tos de final"
JORNADA_4TOS_NUMERO = 1
GRUPO_8VOS_NOMBRE = "8F"
JORNADA_8VOS_NOMBRE = "8vos de final"
JORNADA_8VOS_NUMERO = 1
GRUPO_16AVOS_NOMBRE = "16F"
JORNADA_16AVOS_NOMBRE = "16avos de final"
JORNADA_16AVOS_NUMERO = 1

VALOR_APUESTA_OFICIAL = Decimal("5.00")
VALOR_PREMIO_JORNADA_OFICIAL = Decimal("4.00")
VALOR_ACUMULADO_OFICIAL = Decimal("0.50")
VALOR_UTILIDAD_OFICIAL = Decimal("0.50")

SUMA_DISTRIBUCION_OFICIAL = (
    VALOR_PREMIO_JORNADA_OFICIAL
    + VALOR_ACUMULADO_OFICIAL
    + VALOR_UTILIDAD_OFICIAL
)

if SUMA_DISTRIBUCION_OFICIAL != VALOR_APUESTA_OFICIAL:
    raise ValueError(
        "La distribucion oficial de la apuesta no coincide con el valor total definido."
    )
