import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions import db
from app.models import Apuesta, JornadaGrupo, Partido, Pronostico, Usuario
from app.seeds.seed_inicial import seed_inicial
from app.utils.apuestas import guardar_pronosticos_desde_form
from app.utils.puntos import calcular_puntos_pronostico
from app.utils.ranking import (
    obtener_ranking_general,
    obtener_ranking_por_jornadas,
    recalcular_apuesta,
    recalcular_ranking_jornada,
)


class Semifinales2026Test(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        seed_inicial()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _semifinales(self):
        return JornadaGrupo.query.filter_by(nombre="Semifinales").one()

    def _partidos_semifinales(self):
        return Partido.query.filter_by(jornada_grupo_id=self._semifinales().id).order_by(Partido.numero_calendario).all()

    def _usuario(self, nombres):
        usuario = Usuario(nombres=nombres, apellidos="", email=f"{nombres.lower()}@test.local", activo=True, es_admin=False)
        usuario.set_password("test")
        db.session.add(usuario)
        db.session.flush()
        return usuario

    def _apuesta(self, usuario, jornada, estado_pago="pagado"):
        apuesta = Apuesta(
            usuario_id=usuario.id,
            jornada_grupo_id=jornada.id,
            valor_apostado=jornada.valor_apuesta,
            valor_premio_jornada=jornada.valor_premio_jornada,
            valor_aporte_acumulado=jornada.valor_acumulado,
            valor_utilidad=jornada.valor_utilidad,
            estado_pago=estado_pago,
            puntos_total=0,
            exactos=0,
            aciertos_resultado=0,
            es_valida_para_acumulado=True,
        )
        db.session.add(apuesta)
        db.session.flush()
        return apuesta

    def test_seed_semifinales_idempotente_crea_solo_dos_partidos(self):
        seed_inicial()
        jornada = self._semifinales()
        partidos = self._partidos_semifinales()

        self.assertEqual(len(partidos), 2)
        self.assertEqual(jornada.numero_jornada, 1)
        self.assertEqual(jornada.grupo.nombre, "SF")
        self.assertEqual([p.numero_calendario for p in partidos], [401, 402])
        self.assertEqual([(p.fecha_partido.isoformat(), p.hora_est) for p in partidos], [("2026-07-14", "14:00"), ("2026-07-15", "14:00")])
        self.assertEqual(partidos[0].equipo_local.nombre, "Francia")
        self.assertIn(partidos[0].equipo_visitante.nombre, {"Espana", "España", "EspaÃ±a", "Espa�a"})
        self.assertEqual(partidos[1].equipo_local.nombre, "Inglaterra")
        self.assertEqual(partidos[1].equipo_visitante.nombre, "Argentina")

    def test_cierre_usa_hora_ecuador_y_bloquea_por_partido(self):
        francia_espana, inglaterra_argentina = self._partidos_semifinales()
        antes_primer_partido = datetime(2026, 7, 14, 18, 59, tzinfo=timezone.utc)
        inicio_primer_partido = datetime(2026, 7, 14, 19, 0, tzinfo=timezone.utc)

        self.assertTrue(francia_espana.acepta_pronosticos(antes_primer_partido))
        self.assertFalse(francia_espana.acepta_pronosticos(inicio_primer_partido))
        self.assertTrue(inglaterra_argentina.acepta_pronosticos(inicio_primer_partido))
        self.assertTrue(self._semifinales().esta_abierta_para_apuestas(inicio_primer_partido))

    def test_usuario_pronostica_modifica_y_no_duplica_antes_del_cierre(self):
        jornada = self._semifinales()
        usuario = self._usuario("Ana")
        apuesta = self._apuesta(usuario, jornada)
        francia_espana, inglaterra_argentina = self._partidos_semifinales()

        with patch("app.utils.apuestas.now_ecuador_naive", return_value=datetime(2026, 7, 14, 13, 30)):
            guardar_pronosticos_desde_form(
                apuesta,
                [francia_espana],
                {f"goles_local_{francia_espana.id}": "2", f"goles_visitante_{francia_espana.id}": "1"},
            )
            db.session.flush()
            guardar_pronosticos_desde_form(
                apuesta,
                [inglaterra_argentina],
                {f"goles_local_{inglaterra_argentina.id}": "1", f"goles_visitante_{inglaterra_argentina.id}": "2"},
            )
            db.session.flush()
            guardar_pronosticos_desde_form(
                apuesta,
                [francia_espana],
                {f"goles_local_{francia_espana.id}": "3", f"goles_visitante_{francia_espana.id}": "1"},
            )
            db.session.flush()

        pronosticos = Pronostico.query.filter_by(apuesta_id=apuesta.id).order_by(Pronostico.partido_id).all()
        self.assertEqual(len(pronosticos), 2)
        self.assertEqual((pronosticos[0].goles_local_pred, pronosticos[0].goles_visitante_pred), (3, 1))

    def test_no_modifica_despues_del_inicio_ni_acepta_negativos(self):
        jornada = self._semifinales()
        usuario = self._usuario("Beto")
        apuesta = self._apuesta(usuario, jornada)
        francia_espana = self._partidos_semifinales()[0]

        with patch("app.utils.apuestas.now_ecuador_naive", return_value=datetime(2026, 7, 14, 13, 30)):
            guardar_pronosticos_desde_form(
                apuesta,
                [francia_espana],
                {f"goles_local_{francia_espana.id}": "1", f"goles_visitante_{francia_espana.id}": "0"},
            )
            db.session.flush()
            with self.assertRaisesRegex(ValueError, "marcadores negativos"):
                guardar_pronosticos_desde_form(
                    apuesta,
                    self._partidos_semifinales()[1:],
                    {f"goles_local_{self._partidos_semifinales()[1].id}": "-1", f"goles_visitante_{self._partidos_semifinales()[1].id}": "0"},
                )

        with patch("app.utils.apuestas.now_ecuador_naive", return_value=datetime(2026, 7, 14, 14, 1)):
            with self.assertRaisesRegex(ValueError, "ya est"):
                guardar_pronosticos_desde_form(
                    apuesta,
                    [francia_espana],
                    {f"goles_local_{francia_espana.id}": "4", f"goles_visitante_{francia_espana.id}": "0"},
                )

        pronostico = Pronostico.query.filter_by(apuesta_id=apuesta.id, partido_id=francia_espana.id).one()
        self.assertEqual((pronostico.goles_local_pred, pronostico.goles_visitante_pred), (1, 0))

    def test_reglas_de_puntaje(self):
        self.assertEqual(calcular_puntos_pronostico(2, 1, 2, 1), 5)
        self.assertEqual(calcular_puntos_pronostico(2, 1, 1, 0), 3)
        self.assertEqual(calcular_puntos_pronostico(1, 1, 2, 2), 3)
        self.assertEqual(calcular_puntos_pronostico(0, 2, 1, 0), 0)

    def test_ranking_semifinales_no_mezcla_etapas_y_general_es_idempotente(self):
        jornada_semis = self._semifinales()
        jornada_4tos = JornadaGrupo.query.filter_by(nombre="4tos de final").one()
        francia_espana, inglaterra_argentina = self._partidos_semifinales()
        partido_4tos = Partido.query.filter_by(jornada_grupo_id=jornada_4tos.id).first()

        ana = self._usuario("Ana")
        beto = self._usuario("Beto")
        clara = self._usuario("Clara")

        apuesta_ana_semis = self._apuesta(ana, jornada_semis)
        apuesta_beto_semis = self._apuesta(beto, jornada_semis)
        apuesta_ana_4tos = self._apuesta(ana, jornada_4tos)
        apuesta_clara_4tos = self._apuesta(clara, jornada_4tos)

        db.session.add_all(
            [
                Pronostico(apuesta_id=apuesta_ana_semis.id, partido_id=francia_espana.id, goles_local_pred=2, goles_visitante_pred=1),
                Pronostico(apuesta_id=apuesta_ana_semis.id, partido_id=inglaterra_argentina.id, goles_local_pred=1, goles_visitante_pred=0),
                Pronostico(apuesta_id=apuesta_beto_semis.id, partido_id=francia_espana.id, goles_local_pred=1, goles_visitante_pred=0),
                Pronostico(apuesta_id=apuesta_beto_semis.id, partido_id=inglaterra_argentina.id, goles_local_pred=0, goles_visitante_pred=1),
                Pronostico(apuesta_id=apuesta_ana_4tos.id, partido_id=partido_4tos.id, goles_local_pred=3, goles_visitante_pred=0),
                Pronostico(apuesta_id=apuesta_clara_4tos.id, partido_id=partido_4tos.id, goles_local_pred=3, goles_visitante_pred=0),
            ]
        )
        francia_espana.goles_local = 2
        francia_espana.goles_visitante = 1
        francia_espana.estado = "jugado"
        inglaterra_argentina.goles_local = 1
        inglaterra_argentina.goles_visitante = 1
        inglaterra_argentina.estado = "jugado"
        partido_4tos.goles_local = 3
        partido_4tos.goles_visitante = 0
        partido_4tos.estado = "jugado"
        db.session.flush()

        for apuesta in [apuesta_ana_semis, apuesta_beto_semis, apuesta_ana_4tos, apuesta_clara_4tos]:
            recalcular_apuesta(apuesta.id)
        recalcular_ranking_jornada(jornada_semis.id)
        recalcular_ranking_jornada(jornada_4tos.id)
        db.session.flush()

        ranking_semis = obtener_ranking_por_jornadas((jornada_semis.id,))
        self.assertEqual([(r.nombres, r.puntos, r.exactos, r.aciertos_resultado) for r in ranking_semis], [("Ana", 5, 1, 0), ("Beto", 3, 0, 1)])

        general_1 = [(r.nombres, r.puntos, r.exactos, r.aciertos_resultado) for r in obtener_ranking_general()]
        for apuesta in [apuesta_ana_semis, apuesta_beto_semis, apuesta_ana_4tos, apuesta_clara_4tos]:
            recalcular_apuesta(apuesta.id)
        db.session.flush()
        general_2 = [(r.nombres, r.puntos, r.exactos, r.aciertos_resultado) for r in obtener_ranking_general()]

        self.assertEqual(general_1, general_2)
        self.assertIn(("Ana", 10, 2, 0), general_2)
        self.assertIn(("Beto", 3, 0, 1), general_2)
        self.assertIn(("Clara", 5, 1, 0), general_2)

        francia_espana.goles_local = 1
        francia_espana.goles_visitante = 0
        for apuesta in [apuesta_ana_semis, apuesta_beto_semis]:
            recalcular_apuesta(apuesta.id)
        db.session.flush()
        ranking_corregido = obtener_ranking_por_jornadas((jornada_semis.id,))
        self.assertEqual([(r.nombres, r.puntos) for r in ranking_corregido], [("Beto", 5), ("Ana", 3)])


if __name__ == "__main__":
    unittest.main()
