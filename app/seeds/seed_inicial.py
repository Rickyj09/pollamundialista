from datetime import datetime, date
from app.extensions import db
from app.models import Grupo, Equipo, JornadaGrupo, Partido
from app.constants import (
    GRUPO_4TOS_NOMBRE,
    JORNADA_4TOS_NOMBRE,
    JORNADA_4TOS_NUMERO,
    GRUPO_SEMIFINALES_NOMBRE,
    JORNADA_SEMIFINALES_NOMBRE,
    JORNADA_SEMIFINALES_NUMERO,
    GRUPO_8VOS_NOMBRE,
    JORNADA_8VOS_NOMBRE,
    JORNADA_8VOS_NUMERO,
    GRUPO_16AVOS_NOMBRE,
    JORNADA_16AVOS_NOMBRE,
    JORNADA_16AVOS_NUMERO,
    VALOR_ACUMULADO_OFICIAL,
    VALOR_APUESTA_OFICIAL,
    VALOR_PREMIO_JORNADA_OFICIAL,
    VALOR_UTILIDAD_OFICIAL,
)


def to_date(fecha_str):
    # formato: YYYY-MM-DD
    return datetime.strptime(fecha_str, "%Y-%m-%d").date()


def upsert_grupo(nombre, descripcion=None):
    grupo = Grupo.query.filter_by(nombre=nombre).first()
    if not grupo:
        grupo = Grupo(nombre=nombre, descripcion=descripcion, activo=True)
        db.session.add(grupo)
        db.session.flush()
    return grupo


def upsert_equipo(nombre, grupo, es_sudamericano=False):
    equipo = Equipo.query.filter_by(nombre=nombre).first()
    if not equipo:
        equipo = Equipo(
            nombre=nombre,
            grupo_id=grupo.id,
            es_sudamericano=es_sudamericano,
            activo=True
        )
        db.session.add(equipo)
        db.session.flush()
    return equipo


def upsert_jornada(grupo, numero_jornada, fecha_cierre, nombre=None):
    nombre = nombre or f"Grupo {grupo.nombre} - Jornada {numero_jornada}"
    jornada = JornadaGrupo.query.filter_by(
        grupo_id=grupo.id,
        numero_jornada=numero_jornada
    ).first()

    if not jornada:
        jornada = JornadaGrupo(
            grupo_id=grupo.id,
            numero_jornada=numero_jornada,
            nombre=nombre,
            valor_apuesta=VALOR_APUESTA_OFICIAL,
            valor_premio_jornada=VALOR_PREMIO_JORNADA_OFICIAL,
            valor_acumulado=VALOR_ACUMULADO_OFICIAL,
            valor_utilidad=VALOR_UTILIDAD_OFICIAL,
            fecha_apertura=datetime(2026, 1, 1, 0, 0, 0),
            fecha_cierre=fecha_cierre,
            estado="abierta"
        )
        db.session.add(jornada)
        db.session.flush()

    jornada.nombre = nombre
    jornada.valor_apuesta = VALOR_APUESTA_OFICIAL
    jornada.valor_premio_jornada = VALOR_PREMIO_JORNADA_OFICIAL
    jornada.valor_acumulado = VALOR_ACUMULADO_OFICIAL
    jornada.valor_utilidad = VALOR_UTILIDAD_OFICIAL
    jornada.fecha_cierre = fecha_cierre
    return jornada


def upsert_partido(
    jornada,
    grupo,
    numero_calendario,
    fecha_partido,
    hora_est,
    hora_local,
    equipo_local,
    equipo_visitante,
    estadio,
    ciudad
):
    existe = Partido.query.filter_by(
        jornada_grupo_id=jornada.id,
        numero_calendario=numero_calendario
    ).first()

    if not existe:
        partido = Partido(
            jornada_grupo_id=jornada.id,
            grupo_id=grupo.id,
            numero_calendario=numero_calendario,
            fecha_partido=fecha_partido,
            hora_est=hora_est,
            hora_local=hora_local,
            equipo_local_id=equipo_local.id,
            equipo_visitante_id=equipo_visitante.id,
            estadio=estadio,
            ciudad=ciudad,
            estado="pendiente"
        )
        db.session.add(partido)


def seed_inicial():
    # -------------------------
    # 1. GRUPOS
    # -------------------------
    grupo_c = upsert_grupo("C", "Grupo de Brasil")
    grupo_d = upsert_grupo("D", "Grupo de Paraguay")
    grupo_e = upsert_grupo("E", "Grupo de Ecuador")
    grupo_h = upsert_grupo("H", "Grupo de Uruguay")
    grupo_j = upsert_grupo("J", "Grupo de Argentina")
    grupo_k = upsert_grupo("K", "Grupo de Colombia")
    grupo_4f = upsert_grupo(GRUPO_4TOS_NOMBRE, "Fase eliminatoria - 4tos de final")
    grupo_sf = upsert_grupo(GRUPO_SEMIFINALES_NOMBRE, "Fase eliminatoria - semifinales")
    grupo_8f = upsert_grupo(GRUPO_8VOS_NOMBRE, "Fase eliminatoria - 8vos de final")
    grupo_16f = upsert_grupo(GRUPO_16AVOS_NOMBRE, "Fase eliminatoria - 16avos de final")

    # -------------------------
    # 2. EQUIPOS
    # -------------------------
    # Grupo C
    brasil = upsert_equipo("Brasil", grupo_c, True)
    marruecos = upsert_equipo("Marruecos", grupo_c, False)
    haiti = upsert_equipo("Haití", grupo_c, False)
    escocia = upsert_equipo("Escocia", grupo_c, False)

    # Grupo D
    estados_unidos = upsert_equipo("Estados Unidos", grupo_d, False)
    paraguay = upsert_equipo("Paraguay", grupo_d, True)
    australia = upsert_equipo("Australia", grupo_d, False)
    turquia = upsert_equipo("Turquía", grupo_d, False)

    # Grupo E
    costa_marfil = upsert_equipo("Costa de Marfil", grupo_e, False)
    ecuador = upsert_equipo("Ecuador", grupo_e, True)
    alemania = upsert_equipo("Alemania", grupo_e, False)
    curazao = upsert_equipo("Curazao", grupo_e, False)

    # Grupo H
    arabia = upsert_equipo("Arabia Saudita", grupo_h, False)
    uruguay = upsert_equipo("Uruguay", grupo_h, True)
    cabo_verde = upsert_equipo("Cabo Verde", grupo_h, False)
    espana = upsert_equipo("España", grupo_h, False)

    # Grupo J
    argentina = upsert_equipo("Argentina", grupo_j, True)
    argelia = upsert_equipo("Argelia", grupo_j, False)
    austria = upsert_equipo("Austria", grupo_j, False)
    jordania = upsert_equipo("Jordania", grupo_j, False)

    # Grupo K
    uzbekistan = upsert_equipo("Uzbekistán", grupo_k, False)
    colombia = upsert_equipo("Colombia", grupo_k, True)
    rd_congo = upsert_equipo("República Democrática del Congo", grupo_k, False)
    portugal = upsert_equipo("Portugal", grupo_k, False)

    # Fase 16avos
    sudafrica = upsert_equipo("Sudafrica", grupo_16f, False)
    canada = upsert_equipo("Canada", grupo_16f, False)
    japon = upsert_equipo("Japon", grupo_16f, False)
    paises_bajos = upsert_equipo("Paises Bajos", grupo_16f, False)
    noruega = upsert_equipo("Noruega", grupo_16f, False)
    francia = upsert_equipo("Francia", grupo_16f, False)
    suecia = upsert_equipo("Suecia", grupo_16f, False)
    mexico = upsert_equipo("Mexico", grupo_16f, False)
    inglaterra = upsert_equipo("Inglaterra", grupo_16f, False)
    belgica = upsert_equipo("Belgica", grupo_16f, False)
    senegal = upsert_equipo("Senegal", grupo_16f, False)
    bosnia = upsert_equipo("Bosnia y Herzegovina", grupo_16f, False)
    suiza = upsert_equipo("Suiza", grupo_16f, False)
    croacia = upsert_equipo("Croacia", grupo_16f, False)
    egipto = upsert_equipo("Egipto", grupo_16f, False)
    ghana = upsert_equipo("Ghana", grupo_16f, False)

    # -------------------------
    # 3. JORNADAS
    # fecha_cierre: sugerencia inicial
    # luego puedes cerrarla automáticamente antes del primer partido
    # -------------------------
    jc1 = upsert_jornada(grupo_c, 1, datetime(2026, 6, 13, 17, 59, 0))
    jc2 = upsert_jornada(grupo_c, 2, datetime(2026, 6, 19, 17, 59, 0))
    jc3 = upsert_jornada(grupo_c, 3, datetime(2026, 6, 24, 17, 59, 0))

    jd1 = upsert_jornada(grupo_d, 1, datetime(2026, 6, 12, 20, 59, 0))
    jd2 = upsert_jornada(grupo_d, 2, datetime(2026, 6, 19, 14, 59, 0))
    jd3 = upsert_jornada(grupo_d, 3, datetime(2026, 6, 25, 21, 59, 0))

    je1 = upsert_jornada(grupo_e, 1, datetime(2026, 6, 14, 18, 59, 0))
    je2 = upsert_jornada(grupo_e, 2, datetime(2026, 6, 20, 15, 59, 0))
    je3 = upsert_jornada(grupo_e, 3, datetime(2026, 6, 25, 15, 59, 0))

    jh1 = upsert_jornada(grupo_h, 1, datetime(2026, 6, 15, 17, 59, 0))
    jh2 = upsert_jornada(grupo_h, 2, datetime(2026, 6, 21, 11, 59, 0))
    jh3 = upsert_jornada(grupo_h, 3, datetime(2026, 6, 26, 19, 59, 0))

    jj1 = upsert_jornada(grupo_j, 1, datetime(2026, 6, 16, 19, 59, 0))
    jj2 = upsert_jornada(grupo_j, 2, datetime(2026, 6, 22, 12, 59, 0))
    jj3 = upsert_jornada(grupo_j, 3, datetime(2026, 6, 27, 21, 59, 0))

    jk1 = upsert_jornada(grupo_k, 1, datetime(2026, 6, 17, 12, 59, 0))
    jk2 = upsert_jornada(grupo_k, 2, datetime(2026, 6, 23, 12, 59, 0))
    jk3 = upsert_jornada(grupo_k, 3, datetime(2026, 6, 27, 19, 29, 0))
    j4 = upsert_jornada(
        grupo_4f,
        JORNADA_4TOS_NUMERO,
        datetime(2026, 7, 11, 19, 59, 0),
        nombre=JORNADA_4TOS_NOMBRE,
    )
    jsf = upsert_jornada(
        grupo_sf,
        JORNADA_SEMIFINALES_NUMERO,
        datetime(2026, 7, 19, 13, 59, 0),
        nombre=JORNADA_SEMIFINALES_NOMBRE,
    )
    j8 = upsert_jornada(
        grupo_8f,
        JORNADA_8VOS_NUMERO,
        datetime(2026, 7, 7, 14, 59, 0),
        nombre=JORNADA_8VOS_NOMBRE,
    )
    j16 = upsert_jornada(
        grupo_16f,
        JORNADA_16AVOS_NUMERO,
        datetime(2026, 7, 3, 20, 29, 0),
        nombre=JORNADA_16AVOS_NOMBRE,
    )

    # -------------------------
    # 4. PARTIDOS
    # -------------------------
    # Grupo C
    upsert_partido(jc1, grupo_c, 7, to_date("2026-06-13"), "21:00", "18:00",
                   brasil, marruecos, "Estadio MetLife", "Nueva York/Nueva Jersey")
    upsert_partido(jc1, grupo_c, 5, to_date("2026-06-13"), "21:00", "21:00",
                   haiti, escocia, "Estadio Gillette", "Bostón")

    upsert_partido(jc2, grupo_c, 29, to_date("2026-06-19"), "21:00", "21:00",
                   brasil, haiti, "Campo financiero Lincoln", "Filadelfia")
    upsert_partido(jc2, grupo_c, 30, to_date("2026-06-19"), "18:00", "18:00",
                   escocia, marruecos, "Estadio Gillette", "Bostón")

    upsert_partido(jc3, grupo_c, 49, to_date("2026-06-24"), "18:00", "18:00",
                   escocia, brasil, "Estadio Hard Rock", "Miami")
    upsert_partido(jc3, grupo_c, 50, to_date("2026-06-24"), "18:00", "18:00",
                   marruecos, haiti, "Estadio Mercedes-Benz", "Atlanta")

    # Grupo D
    upsert_partido(jd1, grupo_d, 4, to_date("2026-06-12"), "21:00", "18:00",
                   estados_unidos, paraguay, "Estadio SoFi", "Los Ángeles")
    upsert_partido(jd1, grupo_d, 6, to_date("2026-06-13"), "00:00", "21:00",
                   australia, turquia, "BC Place", "Vancouver")

    upsert_partido(jd2, grupo_d, 31, to_date("2026-06-19"), "00:00", "21:00",
                   turquia, paraguay, "Estadio Levi's", "Área de la Bahía de San Francisco")
    upsert_partido(jd2, grupo_d, 32, to_date("2026-06-19"), "15:00", "12:00",
                   estados_unidos, australia, "Campo de lúmenes", "Seattle")

    upsert_partido(jd3, grupo_d, 59, to_date("2026-06-25"), "22:00", "19:00",
                   turquia, estados_unidos, "Estadio SoFi", "Los Ángeles")
    upsert_partido(jd3, grupo_d, 60, to_date("2026-06-25"), "22:00", "19:00",
                   paraguay, australia, "Estadio Levi's", "Área de la Bahía de San Francisco")

    # Grupo E
    upsert_partido(je1, grupo_e, 9, to_date("2026-06-14"), "19:00", "19:00",
                   costa_marfil, ecuador, "Campo financiero Lincoln", "Filadelfia")
    upsert_partido(je1, grupo_e, 10, to_date("2026-06-14"), "13:00", "12:00",
                   alemania, curazao, "Estadio NRG", "Houston")

    upsert_partido(je2, grupo_e, 33, to_date("2026-06-20"), "16:00", "16:00",
                   alemania, costa_marfil, "Campo BMO", "Toronto")
    upsert_partido(je2, grupo_e, 34, to_date("2026-06-20"), "20:00", "19:00",
                   ecuador, curazao, "Estadio Arrowhead", "Ciudad de Kansas")

    upsert_partido(je3, grupo_e, 55, to_date("2026-06-25"), "16:00", "16:00",
                   curazao, costa_marfil, "Campo financiero Lincoln", "Filadelfia")
    upsert_partido(je3, grupo_e, 56, to_date("2026-06-25"), "16:00", "16:00",
                   ecuador, alemania, "Estadio MetLife", "Nueva York/Nueva Jersey")

    # Grupo H
    upsert_partido(jh1, grupo_h, 13, to_date("2026-06-15"), "18:00", "18:00",
                   arabia, uruguay, "Estadio Hard Rock", "Miami")
    upsert_partido(jh1, grupo_h, 14, to_date("2026-06-15"), "12:00", "12:00",
                   espana, cabo_verde, "Estadio Mercedes-Benz", "Atlanta")

    upsert_partido(jh2, grupo_h, 37, to_date("2026-06-21"), "18:00", "18:00",
                   uruguay, cabo_verde, "Estadio Hard Rock", "Miami")
    upsert_partido(jh2, grupo_h, 38, to_date("2026-06-21"), "12:00", "12:00",
                   espana, arabia, "Estadio Mercedes-Benz", "Atlanta")

    upsert_partido(jh3, grupo_h, 65, to_date("2026-06-26"), "20:00", "19:00",
                   cabo_verde, arabia, "Estadio NRG", "Houston")
    upsert_partido(jh3, grupo_h, 66, to_date("2026-06-26"), "20:00", "18:00",
                   uruguay, espana, "Estadio Akron", "Guadalajara")

    # Grupo J
    upsert_partido(jj1, grupo_j, 19, to_date("2026-06-16"), "21:00", "20:00",
                   argentina, argelia, "Estadio Arrowhead", "Ciudad de Kansas")
    upsert_partido(jj1, grupo_j, 20, to_date("2026-06-16"), "00:00", "21:00",
                   austria, jordania, "Estadio Levi's", "Área de la Bahía de San Francisco")

    upsert_partido(jj2, grupo_j, 43, to_date("2026-06-22"), "13:00", "12:00",
                   argentina, austria, "Estadio AT&T", "Dallas")
    upsert_partido(jj2, grupo_j, 44, to_date("2026-06-22"), "23:00", "20:00",
                   jordania, argelia, "Estadio Levi's", "Área de la Bahía de San Francisco")

    upsert_partido(jj3, grupo_j, 69, to_date("2026-06-27"), "22:00", "21:00",
                   argelia, austria, "Estadio Arrowhead", "Ciudad de Kansas")
    upsert_partido(jj3, grupo_j, 70, to_date("2026-06-27"), "22:00", "21:00",
                   jordania, argentina, "Estadio AT&T", "Dallas")

    # Grupo K
    upsert_partido(jk1, grupo_k, 23, to_date("2026-06-17"), "13:00", "12:00",
                   portugal, rd_congo, "Estadio NRG", "Houston")
    upsert_partido(jk1, grupo_k, 24, to_date("2026-06-17"), "22:00", "20:00",
                   uzbekistan, colombia, "Estadio Azteca", "Ciudad de México")

    upsert_partido(jk2, grupo_k, 47, to_date("2026-06-23"), "13:00", "12:00",
                   portugal, uzbekistan, "Estadio NRG", "Houston")
    upsert_partido(jk2, grupo_k, 48, to_date("2026-06-23"), "22:00", "20:00",
                   colombia, rd_congo, "Estadio Akron", "Guadalajara")

    upsert_partido(jk3, grupo_k, 71, to_date("2026-06-27"), "19:30", "19:30",
                   colombia, portugal, "Estadio Hard Rock", "Miami")
    upsert_partido(jk3, grupo_k, 72, to_date("2026-06-27"), "19:30", "19:30",
                   rd_congo, uzbekistan, "Estadio Mercedes-Benz", "Atlanta")

    # 4tos de final
    upsert_partido(j4, grupo_4f, 301, to_date("2026-07-09"), "15:00", "15:00",
                   francia, marruecos, "Pendiente", "Pendiente")
    upsert_partido(j4, grupo_4f, 302, to_date("2026-07-10"), "14:00", "14:00",
                   espana, belgica, "Pendiente", "Pendiente")
    upsert_partido(j4, grupo_4f, 303, to_date("2026-07-11"), "16:00", "16:00",
                   noruega, inglaterra, "Pendiente", "Pendiente")
    upsert_partido(j4, grupo_4f, 304, to_date("2026-07-11"), "20:00", "20:00",
                   argentina, suiza, "Pendiente", "Pendiente")

    # Semifinales
    upsert_partido(jsf, grupo_sf, 401, to_date("2026-07-14"), "14:00", "14:00",
                   francia, espana, "Pendiente", "Pendiente")
    upsert_partido(jsf, grupo_sf, 402, to_date("2026-07-15"), "14:00", "14:00",
                   inglaterra, argentina, "Pendiente", "Pendiente")
    upsert_partido(jsf, grupo_sf, 403, to_date("2026-07-18"), "16:00", "16:00",
                   francia, inglaterra, "Pendiente", "Pendiente")
    upsert_partido(jsf, grupo_sf, 404, to_date("2026-07-19"), "14:00", "14:00",
                   espana, argentina, "Pendiente", "Pendiente")

    # 8vos de final
    upsert_partido(j8, grupo_8f, 201, to_date("2026-07-04"), "12:00", "12:00",
                   canada, marruecos, "Pendiente", "Pendiente")
    upsert_partido(j8, grupo_8f, 202, to_date("2026-07-04"), "16:00", "16:00",
                   paraguay, francia, "Pendiente", "Pendiente")
    upsert_partido(j8, grupo_8f, 203, to_date("2026-07-05"), "15:00", "15:00",
                   brasil, noruega, "Pendiente", "Pendiente")
    upsert_partido(j8, grupo_8f, 204, to_date("2026-07-05"), "19:00", "19:00",
                   mexico, inglaterra, "Pendiente", "Pendiente")
    upsert_partido(j8, grupo_8f, 205, to_date("2026-07-06"), "14:00", "14:00",
                   portugal, espana, "Pendiente", "Pendiente")
    upsert_partido(j8, grupo_8f, 206, to_date("2026-07-06"), "19:00", "19:00",
                   estados_unidos, belgica, "Pendiente", "Pendiente")
    upsert_partido(j8, grupo_8f, 207, to_date("2026-07-07"), "11:00", "11:00",
                   argentina, egipto, "Pendiente", "Pendiente")
    upsert_partido(j8, grupo_8f, 208, to_date("2026-07-07"), "15:00", "15:00",
                   suiza, colombia, "Pendiente", "Pendiente")

    # 16avos de final
    upsert_partido(j16, grupo_16f, 101, to_date("2026-06-28"), "14:00", "14:00",
                   sudafrica, canada, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 102, to_date("2026-06-29"), "12:00", "12:00",
                   brasil, japon, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 103, to_date("2026-06-29"), "15:30", "15:30",
                   alemania, paraguay, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 104, to_date("2026-06-29"), "20:00", "20:00",
                   paises_bajos, marruecos, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 105, to_date("2026-06-30"), "12:00", "12:00",
                   costa_marfil, noruega, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 106, to_date("2026-06-30"), "16:00", "16:00",
                   francia, suecia, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 107, to_date("2026-06-30"), "20:00", "20:00",
                   mexico, ecuador, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 108, to_date("2026-07-01"), "11:00", "11:00",
                   inglaterra, rd_congo, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 109, to_date("2026-07-01"), "15:00", "15:00",
                   belgica, senegal, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 110, to_date("2026-07-01"), "19:00", "19:00",
                   estados_unidos, bosnia, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 111, to_date("2026-07-02"), "14:00", "14:00",
                   espana, austria, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 112, to_date("2026-07-02"), "18:00", "18:00",
                   portugal, croacia, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 113, to_date("2026-07-02"), "22:00", "22:00",
                   suiza, argelia, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 114, to_date("2026-07-03"), "13:00", "13:00",
                   australia, egipto, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 115, to_date("2026-07-03"), "17:00", "17:00",
                   argentina, cabo_verde, "Pendiente", "Pendiente")
    upsert_partido(j16, grupo_16f, 116, to_date("2026-07-03"), "20:30", "20:30",
                   colombia, ghana, "Pendiente", "Pendiente")

    db.session.commit()
    print("Seed inicial cargado correctamente.")
