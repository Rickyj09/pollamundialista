import os
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions import db
from app.models import Apuesta, JornadaGrupo, PagoJornada, Partido, Pronostico, Usuario
from app.seeds.seed_inicial import seed_inicial
from app.utils.apuestas import (
    guardar_pronosticos_desde_form,
    usuario_tiene_pago_confirmado,
)
from app.utils.pozo import (
    detectar_ganador_jornada,
    jornada_completa_y_calculada,
    recalcular_pozo_jornada,
)
from app.utils.puntos import calcular_puntos_pronostico
from app.utils.ranking import (
    obtener_ranking_general,
    obtener_ranking_por_jornadas,
    recalcular_apuesta,
    recalcular_ranking_jornada,
)


ESPANA_VARIANTS = {"Espana", "Espa\u00f1a", "EspaÃ±a", "EspaÃƒÂ±a", "Espaï¿½a"}


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
        return (
            Partido.query
            .filter_by(jornada_grupo_id=self._semifinales().id)
            .order_by(Partido.numero_calendario)
            .all()
        )

    def _partidos_por_calendario(self):
        return {partido.numero_calendario: partido for partido in self._partidos_semifinales()}

    def _usuario(self, nombres, apellidos=""):
        usuario = Usuario(
            nombres=nombres,
            apellidos=apellidos,
            email=f"{nombres.lower()}-{apellidos.lower() or 'x'}@test.local",
            activo=True,
            es_admin=False,
        )
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

    def _pago(self, usuario, jornada, estado="confirmado"):
        pago = PagoJornada(
            usuario_id=usuario.id,
            jornada_grupo_id=jornada.id,
            valor=jornada.valor_apuesta,
            estado=estado,
            metodo_pago="manual",
        )
        db.session.add(pago)
        db.session.flush()
        return pago

    def _pronostico(self, apuesta, partido, local, visitante):
        pronostico = Pronostico(
            apuesta_id=apuesta.id,
            partido_id=partido.id,
            goles_local_pred=local,
            goles_visitante_pred=visitante,
            puntos_obtenidos=0,
        )
        db.session.add(pronostico)
        db.session.flush()
        return pronostico

    def _liquidar(self, partido, local, visitante):
        partido.goles_local = local
        partido.goles_visitante = visitante
        partido.estado = "jugado"
        db.session.flush()

    def _recalcular_apuestas(self, *apuestas):
        for apuesta in apuestas:
            recalcular_apuesta(apuesta.id)
        recalcular_ranking_jornada(self._semifinales().id)
        db.session.flush()

    def _login(self, client, usuario):
        return client.post(
            "/auth/login",
            data={"email": usuario.email, "password": "test"},
            follow_redirects=False,
        )

    def test_seed_semifinales_idempotente_crea_cuatro_partidos(self):
        jornada_id = self._semifinales().id
        equipos_antes = {equipo.nombre for equipo in db.session.query(Partido.equipo_local.property.mapper.class_).all()}

        seed_inicial()
        seed_inicial()

        jornada = self._semifinales()
        partidos = self._partidos_semifinales()
        equipos_despues = {equipo.nombre for equipo in db.session.query(Partido.equipo_local.property.mapper.class_).all()}

        self.assertEqual(jornada.id, jornada_id)
        self.assertEqual(jornada.numero_jornada, 1)
        self.assertEqual(jornada.grupo.nombre, "SF")
        self.assertEqual(jornada.fecha_cierre, datetime(2026, 7, 19, 13, 59))
        self.assertEqual(len(partidos), 4)
        self.assertEqual([p.numero_calendario for p in partidos], [401, 402, 403, 404])
        self.assertEqual(equipos_antes, equipos_despues)

        datos = [
            (p.numero_calendario, p.fecha_partido.isoformat(), p.hora_est, p.equipo_local.nombre, p.equipo_visitante.nombre)
            for p in partidos
        ]
        self.assertEqual(datos[0][:4], (401, "2026-07-14", "14:00", "Francia"))
        self.assertIn(datos[0][4], ESPANA_VARIANTS)
        self.assertEqual(datos[1], (402, "2026-07-15", "14:00", "Inglaterra", "Argentina"))
        self.assertEqual(datos[2], (403, "2026-07-18", "16:00", "Francia", "Inglaterra"))
        self.assertIn(datos[3][3], ESPANA_VARIANTS)
        self.assertEqual(datos[3][:3] + datos[3][4:], (404, "2026-07-19", "14:00", "Argentina"))

        ids_por_calendario = {p.numero_calendario: p.id for p in partidos}
        self.assertNotEqual(ids_por_calendario[403], 403)
        self.assertNotEqual(ids_por_calendario[404], 404)

    def test_migracion_es_lineal_idempotente_y_no_usa_ids_primarios_fijos(self):
        migration = Path("migrations/versions/a7c8d9e0f1a2_agregar_tercer_puesto_y_final_a_semifinales.py")
        contenido = migration.read_text(encoding="utf-8")

        self.assertIn('revision = "a7c8d9e0f1a2"', contenido)
        self.assertIn('down_revision = "f0b1c2d3e4f5"', contenido)
        self.assertIn("numero_calendario = 403", contenido)
        self.assertIn("numero_calendario = 404", contenido)
        self.assertIn("JOIN equipos local ON local.nombre = 'Francia'", contenido)
        self.assertIn("JOIN equipos visitante ON visitante.nombre = 'Inglaterra'", contenido)
        self.assertIn("JOIN equipos visitante ON visitante.nombre = 'Argentina'", contenido)
        self.assertIn("g.nombre = 'SF'", contenido)
        self.assertIn("j.numero_jornada = 1", contenido)
        self.assertIn("NOT EXISTS", contenido)
        self.assertNotIn("INSERT INTO apuestas", contenido)
        self.assertNotIn("INSERT INTO pronosticos", contenido)
        self.assertNotIn("INSERT INTO pagos_jornada", contenido)
        self.assertNotIn("UPDATE apuestas", contenido)
        self.assertNotIn("UPDATE pronosticos", contenido)
        self.assertNotIn("UPDATE pagos_jornada", contenido)

    def test_cierre_usa_hora_ecuador_y_bloquea_por_partido(self):
        partidos = self._partidos_por_calendario()
        antes_primera_semi = datetime(2026, 7, 14, 18, 59, tzinfo=timezone.utc)
        inicio_primera_semi = datetime(2026, 7, 14, 19, 0, tzinfo=timezone.utc)
        antes_tercer_puesto = datetime(2026, 7, 18, 20, 59, tzinfo=timezone.utc)
        inicio_tercer_puesto = datetime(2026, 7, 18, 21, 0, tzinfo=timezone.utc)
        antes_final = datetime(2026, 7, 19, 18, 59, tzinfo=timezone.utc)
        inicio_final = datetime(2026, 7, 19, 19, 0, tzinfo=timezone.utc)

        self.assertTrue(partidos[401].acepta_pronosticos(antes_primera_semi))
        self.assertFalse(partidos[401].acepta_pronosticos(inicio_primera_semi))
        self.assertTrue(partidos[402].acepta_pronosticos(inicio_primera_semi))
        self.assertFalse(partidos[403].acepta_pronosticos(inicio_tercer_puesto))
        self.assertTrue(partidos[403].acepta_pronosticos(antes_tercer_puesto))
        self.assertTrue(partidos[404].acepta_pronosticos(antes_final))
        self.assertFalse(partidos[404].acepta_pronosticos(inicio_final))
        self.assertTrue(self._semifinales().esta_abierta_para_apuestas(inicio_primera_semi))

    def test_reabrir_jornada_no_reabre_partidos_ya_iniciados(self):
        jornada = self._semifinales()
        partidos = self._partidos_por_calendario()
        usuario = self._usuario("Beto")
        apuesta = self._apuesta(usuario, jornada)
        self._pronostico(apuesta, partidos[401], 1, 0)
        jornada.estado = "abierta"
        db.session.flush()

        with patch("app.utils.apuestas.now_ecuador_naive", return_value=datetime(2026, 7, 16, 10, 0)):
            with self.assertRaisesRegex(ValueError, "ya est"):
                guardar_pronosticos_desde_form(
                    apuesta,
                    [partidos[401]],
                    {f"goles_local_{partidos[401].id}": "4", f"goles_visitante_{partidos[401].id}": "0"},
                )
            with self.assertRaisesRegex(ValueError, "ya est"):
                guardar_pronosticos_desde_form(
                    apuesta,
                    [partidos[402]],
                    {f"goles_local_{partidos[402].id}": "3", f"goles_visitante_{partidos[402].id}": "0"},
                )
            resultado = guardar_pronosticos_desde_form(
                apuesta,
                [partidos[403]],
                {f"goles_local_{partidos[403].id}": "2", f"goles_visitante_{partidos[403].id}": "1"},
            )

        self.assertEqual(resultado["creados"], 1)

    def test_usuario_pronostica_modifica_y_no_duplica_antes_del_cierre(self):
        jornada = self._semifinales()
        usuario = self._usuario("Ana")
        apuesta = self._apuesta(usuario, jornada)
        partidos = self._partidos_por_calendario()

        with patch("app.utils.apuestas.now_ecuador_naive", return_value=datetime(2026, 7, 18, 15, 30)):
            guardar_pronosticos_desde_form(
                apuesta,
                [partidos[403]],
                {f"goles_local_{partidos[403].id}": "2", f"goles_visitante_{partidos[403].id}": "1"},
            )
            db.session.flush()
            guardar_pronosticos_desde_form(
                apuesta,
                [partidos[404]],
                {f"goles_local_{partidos[404].id}": "1", f"goles_visitante_{partidos[404].id}": "2"},
            )
            db.session.flush()
            guardar_pronosticos_desde_form(
                apuesta,
                [partidos[403]],
                {f"goles_local_{partidos[403].id}": "3", f"goles_visitante_{partidos[403].id}": "1"},
            )
            db.session.flush()

        pronosticos = Pronostico.query.filter_by(apuesta_id=apuesta.id).order_by(Pronostico.partido_id).all()
        self.assertEqual(len(pronosticos), 2)
        self.assertEqual((pronosticos[0].goles_local_pred, pronosticos[0].goles_visitante_pred), (3, 1))

    def test_pago_confirmado_permite_nuevos_partidos_sin_segundo_pago(self):
        jornada = self._semifinales()
        usuario = self._usuario("Carla")
        self._pago(usuario, jornada, estado="confirmado")
        apuesta = self._apuesta(usuario, jornada, estado_pago="pagado")
        partido = self._partidos_por_calendario()[403]

        self.assertTrue(usuario_tiene_pago_confirmado(usuario.id, jornada.id))

        with patch("app.utils.apuestas.now_ecuador_naive", return_value=datetime(2026, 7, 18, 15, 30)):
            guardar_pronosticos_desde_form(
                apuesta,
                [partido],
                {f"goles_local_{partido.id}": "1", f"goles_visitante_{partido.id}": "0"},
            )
            db.session.flush()

        self.assertEqual(PagoJornada.query.filter_by(usuario_id=usuario.id, jornada_grupo_id=jornada.id).count(), 1)
        self.assertEqual(Apuesta.query.filter_by(usuario_id=usuario.id, jornada_grupo_id=jornada.id).count(), 1)

    def test_usuario_sin_pago_mantiene_comportamiento_vigente_en_rutas(self):
        usuario = self._usuario("Diego")
        client = self.app.test_client()

        response = client.get("/apuestas/semifinales", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

        self._login(client, usuario)
        response = client.get("/apuestas/semifinales")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pago pendiente", response.data)

    def test_rutas_semifinales_muestran_cuatro_partidos_y_nuevos_formularios(self):
        usuario = self._usuario("Elena")
        self._pago(usuario, self._semifinales(), estado="confirmado")
        self._apuesta(usuario, self._semifinales(), estado_pago="pagado")
        partidos = self._partidos_por_calendario()
        client = self.app.test_client()
        self._login(client, usuario)

        listado = client.get("/apuestas/semifinales")
        self.assertEqual(listado.status_code, 200)
        self.assertIn(b"Francia", listado.data)
        self.assertIn(b"Inglaterra", listado.data)
        self.assertIn(b"Argentina", listado.data)

        for numero in (403, 404):
            detalle = client.get(f"/apuestas/semifinales/partido/{partidos[numero].id}")
            self.assertEqual(detalle.status_code, 200)

        ranking = client.get("/resultados/semifinales")
        self.assertEqual(ranking.status_code, 200)
        self.assertIn(b"cuatro partidos", ranking.data)

    def test_reglas_de_puntaje(self):
        self.assertEqual(calcular_puntos_pronostico(2, 1, 2, 1), 5)
        self.assertEqual(calcular_puntos_pronostico(2, 1, 1, 0), 3)
        self.assertEqual(calcular_puntos_pronostico(1, 1, 2, 2), 3)
        self.assertEqual(calcular_puntos_pronostico(0, 2, 1, 0), 0)

    def test_ranking_semifinales_suma_cuatro_partidos_y_recalculo_no_duplica(self):
        jornada = self._semifinales()
        partidos = self._partidos_por_calendario()
        ana = self._usuario("Ana")
        beto = self._usuario("Beto")
        apuesta_ana = self._apuesta(ana, jornada)
        apuesta_beto = self._apuesta(beto, jornada)

        pronosticos = [
            (apuesta_ana, 401, 2, 1),
            (apuesta_ana, 402, 1, 1),
            (apuesta_ana, 403, 2, 0),
            (apuesta_ana, 404, 1, 0),
            (apuesta_beto, 401, 1, 0),
            (apuesta_beto, 402, 0, 1),
            (apuesta_beto, 403, 2, 1),
            (apuesta_beto, 404, 0, 2),
        ]
        for apuesta, numero, local, visitante in pronosticos:
            self._pronostico(apuesta, partidos[numero], local, visitante)

        self._liquidar(partidos[401], 2, 1)
        self._recalcular_apuestas(apuesta_ana, apuesta_beto)
        self.assertEqual((apuesta_ana.puntos_total, apuesta_ana.exactos, apuesta_ana.aciertos_resultado), (5, 1, 0))
        self.assertEqual((apuesta_beto.puntos_total, apuesta_beto.exactos, apuesta_beto.aciertos_resultado), (3, 0, 1))

        self._liquidar(partidos[402], 1, 1)
        self._recalcular_apuestas(apuesta_ana, apuesta_beto)
        self.assertEqual((apuesta_ana.puntos_total, apuesta_ana.exactos, apuesta_ana.aciertos_resultado), (10, 2, 0))
        self.assertEqual((apuesta_beto.puntos_total, apuesta_beto.exactos, apuesta_beto.aciertos_resultado), (3, 0, 1))

        self._liquidar(partidos[403], 2, 1)
        self._recalcular_apuestas(apuesta_ana, apuesta_beto)
        self.assertEqual((apuesta_ana.puntos_total, apuesta_ana.exactos, apuesta_ana.aciertos_resultado), (13, 2, 1))
        self.assertEqual((apuesta_beto.puntos_total, apuesta_beto.exactos, apuesta_beto.aciertos_resultado), (8, 1, 1))

        self._liquidar(partidos[404], 1, 0)
        self._recalcular_apuestas(apuesta_ana, apuesta_beto)
        ranking = obtener_ranking_por_jornadas((jornada.id,))
        self.assertEqual([(r.nombres, r.puntos, r.exactos, r.aciertos_resultado) for r in ranking], [("Ana", 18, 3, 1), ("Beto", 8, 1, 1)])

        recalcular_apuesta(apuesta_ana.id)
        recalcular_apuesta(apuesta_beto.id)
        db.session.flush()
        self.assertEqual((apuesta_ana.puntos_total, apuesta_beto.puntos_total), (18, 8))

        partidos[401].goles_local = 1
        partidos[401].goles_visitante = 0
        self._recalcular_apuestas(apuesta_ana, apuesta_beto)
        ranking_corregido = obtener_ranking_por_jornadas((jornada.id,))
        self.assertEqual([(r.nombres, r.puntos) for r in ranking_corregido], [("Ana", 16), ("Beto", 10)])

    def test_ranking_general_conserva_historico_y_suma_finales_sin_duplicar(self):
        jornada_semis = self._semifinales()
        jornada_4tos = JornadaGrupo.query.filter_by(nombre="4tos de final").one()
        partidos = self._partidos_por_calendario()
        partido_4tos = Partido.query.filter_by(jornada_grupo_id=jornada_4tos.id).first()

        ana = self._usuario("Ana")
        beto = self._usuario("Beto")
        clara = self._usuario("Clara")
        apuesta_ana_semis = self._apuesta(ana, jornada_semis)
        apuesta_beto_semis = self._apuesta(beto, jornada_semis)
        apuesta_ana_4tos = self._apuesta(ana, jornada_4tos)
        apuesta_clara_4tos = self._apuesta(clara, jornada_4tos)

        self._pronostico(apuesta_ana_semis, partidos[403], 2, 1)
        self._pronostico(apuesta_beto_semis, partidos[403], 1, 0)
        self._pronostico(apuesta_ana_4tos, partido_4tos, 3, 0)
        self._pronostico(apuesta_clara_4tos, partido_4tos, 3, 0)
        self._liquidar(partidos[403], 2, 1)
        self._liquidar(partido_4tos, 3, 0)
        self._recalcular_apuestas(apuesta_ana_semis, apuesta_beto_semis)
        recalcular_apuesta(apuesta_ana_4tos.id)
        recalcular_apuesta(apuesta_clara_4tos.id)
        db.session.flush()

        general_1 = [(r.nombres, r.puntos, r.exactos, r.aciertos_resultado) for r in obtener_ranking_general()]
        recalcular_apuesta(apuesta_ana_semis.id)
        recalcular_apuesta(apuesta_beto_semis.id)
        db.session.flush()
        general_2 = [(r.nombres, r.puntos, r.exactos, r.aciertos_resultado) for r in obtener_ranking_general()]

        self.assertEqual(general_1, general_2)
        self.assertIn(("Ana", 10, 2, 0), general_2)
        self.assertIn(("Beto", 3, 0, 1), general_2)
        self.assertIn(("Clara", 5, 1, 0), general_2)

        partidos[403].goles_local = 1
        partidos[403].goles_visitante = 0
        self._recalcular_apuestas(apuesta_ana_semis, apuesta_beto_semis)
        general_corregido = [(r.nombres, r.puntos) for r in obtener_ranking_general()]
        self.assertIn(("Ana", 8), general_corregido)
        self.assertIn(("Beto", 5), general_corregido)

    def test_jornada_reabierta_conserva_datos_y_se_liquida_al_completar_cuatro_partidos(self):
        jornada = self._semifinales()
        partidos = self._partidos_por_calendario()
        ana = self._usuario("Ana")
        beto = self._usuario("Beto")
        self._pago(ana, jornada, "confirmado")
        self._pago(beto, jornada, "pendiente")
        apuesta_ana = self._apuesta(ana, jornada, "pagado")
        apuesta_beto = self._apuesta(beto, jornada, "pendiente")
        for apuesta in (apuesta_ana, apuesta_beto):
            self._pronostico(apuesta, partidos[401], 2, 1)
            self._pronostico(apuesta, partidos[402], 1, 1)
            self._pronostico(apuesta, partidos[403], 2, 1)
            self._pronostico(apuesta, partidos[404], 1, 0)

        self._liquidar(partidos[401], 2, 1)
        self._liquidar(partidos[402], 1, 1)
        self._recalcular_apuestas(apuesta_ana, apuesta_beto)
        puntos_antes = (apuesta_ana.puntos_total, apuesta_ana.exactos, apuesta_ana.aciertos_resultado)
        jornada.estado = "liquidada"
        jornada.estado_ganador = "definido"
        jornada.ganador_apuesta_id = apuesta_ana.id
        db.session.flush()

        jornada.estado = "abierta"
        jornada.estado_ganador = "pendiente"
        jornada.ganador_apuesta_id = None
        db.session.flush()

        self.assertEqual((apuesta_ana.puntos_total, apuesta_ana.exactos, apuesta_ana.aciertos_resultado), puntos_antes)
        self.assertEqual(PagoJornada.query.filter_by(jornada_grupo_id=jornada.id).count(), 2)
        self.assertFalse(jornada_completa_y_calculada(jornada))
        recalcular_pozo_jornada(jornada.id)
        self.assertEqual(jornada.total_jugadores_confirmados, 1)
        self.assertEqual(Decimal(str(jornada.pozo_premio)), Decimal("4.00"))

        self._liquidar(partidos[403], 2, 1)
        self.assertFalse(jornada_completa_y_calculada(jornada))
        self._liquidar(partidos[404], 1, 0)
        self.assertTrue(jornada_completa_y_calculada(jornada))
        self._recalcular_apuestas(apuesta_ana, apuesta_beto)
        ganador = detectar_ganador_jornada(jornada.id)
        jornada.estado = "liquidada"
        db.session.flush()

        self.assertEqual(ganador.id, apuesta_ana.id)
        self.assertEqual(jornada.ganador_apuesta_id, apuesta_ana.id)
        self.assertEqual(jornada.estado_ganador, "definido")
        self.assertEqual(jornada.estado, "liquidada")


if __name__ == "__main__":
    unittest.main()
