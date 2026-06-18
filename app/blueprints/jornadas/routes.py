from flask import render_template
from sqlalchemy.orm import joinedload, selectinload
from app.blueprints.jornadas import jornadas_bp
from app.models import JornadaGrupo, Apuesta, Partido, Pronostico, Usuario


@jornadas_bp.route("/")
def listar():
    jornadas = (
        JornadaGrupo.query
        .options(joinedload(JornadaGrupo.grupo))
        .order_by(JornadaGrupo.fecha_cierre.asc(), JornadaGrupo.id.asc())
        .all()
    )
    return render_template("jornadas/listar_v2.html", jornadas=jornadas)


@jornadas_bp.route("/<int:jornada_id>")
def detalle(jornada_id):
    jornada = (
        JornadaGrupo.query
        .options(
            joinedload(JornadaGrupo.grupo),
            selectinload(JornadaGrupo.partidos).joinedload(Partido.equipo_local),
            selectinload(JornadaGrupo.partidos).joinedload(Partido.equipo_visitante),
        )
        .filter_by(id=jornada_id)
        .first_or_404()
    )

    partidos = sorted(
        jornada.partidos,
        key=lambda partido: (
            partido.fecha_partido,
            partido.numero_calendario or 0,
            partido.id,
        ),
    )

    pronosticos_visibles = jornada.pronosticos_son_visibles()
    pronosticos_por_partido = []

    if pronosticos_visibles:
        apuestas = (
            Apuesta.query
            .join(Usuario, Usuario.id == Apuesta.usuario_id)
            .options(
                joinedload(Apuesta.usuario),
                selectinload(Apuesta.pronosticos)
                .joinedload(Pronostico.partido)
                .joinedload(Partido.equipo_local),
                selectinload(Apuesta.pronosticos)
                .joinedload(Pronostico.partido)
                .joinedload(Partido.equipo_visitante),
            )
            .filter(Apuesta.jornada_grupo_id == jornada.id)
            .order_by(Usuario.id.asc(), Apuesta.id.asc())
            .all()
        )

        filas_por_partido = {partido.id: [] for partido in partidos}

        for apuesta in apuestas:
            for pronostico in apuesta.pronosticos:
                filas_por_partido.setdefault(pronostico.partido_id, []).append(
                    {
                        "usuario": apuesta.usuario,
                        "estado_pago": (apuesta.estado_pago or "").strip(),
                        "pronostico": pronostico,
                    }
                )

        for partido in partidos:
            filas = sorted(
                filas_por_partido.get(partido.id, []),
                key=lambda fila: (fila["usuario"].id, fila["pronostico"].id),
            )
            pronosticos_por_partido.append(
                {
                    "partido": partido,
                    "filas": filas,
                }
            )

    return render_template(
        "jornadas/detalle_v2.html",
        jornada=jornada,
        partidos=partidos,
        pronosticos_visibles=pronosticos_visibles,
        pronosticos_por_partido=pronosticos_por_partido,
    )
