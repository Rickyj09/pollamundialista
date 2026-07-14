from datetime import date, timedelta
from types import SimpleNamespace
import unittest

from app.models.partido import Partido
from app.models.pronostico import Pronostico
from app.utils.apuestas import guardar_pronosticos_desde_form
from app.utils.timezone import now_ecuador_naive


def make_partido(*, estado="pendiente", dias=1, hora="23:59"):
    return Partido(
        id=79,
        jornada_grupo_id=1,
        grupo_id=1,
        fecha_partido=date.today() + timedelta(days=dias),
        hora_est=hora,
        equipo_local_id=1,
        equipo_visitante_id=2,
        estado=estado,
    )


class ApuestasCierrePartidoTest(unittest.TestCase):
    def test_partido_futuro_pendiente_permite_pronosticar(self):
        partido = make_partido(estado=" pendiente ", dias=1)

        self.assertTrue(partido.acepta_pronosticos(now_ecuador_naive()))

    def test_partido_futuro_cerrado_no_permite_pronosticar(self):
        partido = make_partido(estado=" Cerrado ", dias=1)

        self.assertFalse(partido.acepta_pronosticos(now_ecuador_naive()))

    def test_partido_iniciado_no_permite_pronosticar(self):
        partido = make_partido(estado="pendiente", dias=-1)

        self.assertFalse(partido.acepta_pronosticos(now_ecuador_naive()))

    def test_post_directo_a_partido_cerrado_no_modifica_pronostico(self):
        partido = make_partido(estado="cerrado", dias=1)
        pronostico = Pronostico(
            apuesta_id=1,
            partido_id=partido.id,
            goles_local_pred=1,
            goles_visitante_pred=0,
            puntos_obtenidos=0,
        )
        apuesta = SimpleNamespace(pronosticos=[pronostico])

        with self.assertRaisesRegex(ValueError, "Este partido ya está cerrado"):
            guardar_pronosticos_desde_form(
                apuesta=apuesta,
                partidos=[partido],
                form_data={
                    f"goles_local_{partido.id}": "4",
                    f"goles_visitante_{partido.id}": "3",
                },
            )

        self.assertEqual(pronostico.goles_local_pred, 1)
        self.assertEqual(pronostico.goles_visitante_pred, 0)


if __name__ == "__main__":
    unittest.main()
