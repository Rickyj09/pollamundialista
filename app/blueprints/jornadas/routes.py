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

    pronosticos_visibles = jornada.estado in {"cerrada", "liquidada"}
    apuestas_por_usuario = []

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

        for apuesta in apuestas:
            pronosticos_ordenados = sorted(
                apuesta.pronosticos,
                key=lambda pronostico: (
                    pronostico.partido.fecha_partido,
                    pronostico.partido.numero_calendario or 0,
                    pronostico.partido.id,
                ),
            )

            if pronosticos_ordenados:
                apuestas_por_usuario.append(
                    {
                        "usuario": apuesta.usuario,
                        "apuesta": apuesta,
                        "pronosticos": pronosticos_ordenados,
                    }
                )

    return render_template(
        "jornadas/detalle_v2.html",
        jornada=jornada,
        partidos=partidos,
        pronosticos_visibles=pronosticos_visibles,
        apuestas_por_usuario=apuestas_por_usuario,
    )
