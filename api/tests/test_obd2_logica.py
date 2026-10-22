from unittest import mock

from django.test import SimpleTestCase, TestCase

from api.obd2 import (calcular_nivel, crear_alerta_si_corresponde, estado_por_nivel, redondear, redondear_dos,
                      unidad_de, valor_simulado)
from core.models import Alerta


class CalcularNivelTests(SimpleTestCase):
    def test_casos_calculados_a_mano(self):
        casos = [("TEMP", 95, 75), ("RPM", 600, 0), ("RPM", 599, 0), ("RPM", 3000, 100), ("RPM", 5000, 100),
                 ("RPM", 1800, 50), ("VELOCIDAD", 2.5, 3), ("O2", 0.5, 50), ("FUEL", 50, 50), ("OIL", 3, 50),
                 ("MAF", 5, 50), ("ECT", 90, 90), ("MAP", 1.0, 1), ("DESCONOCIDO", 42.4, 42)]
        for tipo, valor, esperado in casos:
            self.assertEqual(calcular_nivel(tipo, valor), esperado, (tipo, valor))


class SimulacionTests(SimpleTestCase):
    def test_limites_del_valor_simulado(self):
        minimos = {"MAF": 2.0, "O2": 0.1, "ECT": 75.0, "MAP": 0.5, "RPM": 650.0, "VELOCIDAD": 0.0, "TEMP": 75.0,
                   "OIL": 1.0, "FUEL": 15.0, None: 0.0}
        maximos = {"MAF": 12.0, "O2": 1.2, "ECT": 130.0, "MAP": 1.2, "RPM": 4450.0, "VELOCIDAD": 120.0, "TEMP": 130.0,
                   "OIL": 6.0, "FUEL": 95.0, None: 100.0}
        for azar, esperados in ((0.0, minimos), (0.9999999, maximos)):
            with mock.patch("api.obd2.random.random", return_value=azar):
                for tipo, esperado in esperados.items():
                    valor = valor_simulado(tipo)
                    self.assertIsInstance(valor, float)
                    self.assertEqual(valor, esperado, tipo)

    def test_unidades_y_redondeo(self):
        self.assertEqual([unidad_de(t) for t in ("RPM", "VELOCIDAD", "TEMP", "ECT", "MAF", "O2", "OIL", "FUEL", "MAP", None)],
                         ["rpm", "km/h", "°C", "°C", "g/s", "V", "bar", "%", "", ""])
        self.assertEqual((redondear(2.25), redondear_dos(0.125)), (2.3, 0.13))
        self.assertEqual([estado_por_nivel(n) for n in (39, 40, 69, 70)], ["OK", "ADVERTENCIA", "ADVERTENCIA", "FALLA"])


class AlertasTests(TestCase):
    def test_crea_alerta_de_falla_y_notifica(self):
        with self.assertLogs("autosen.observador", level="WARNING"):
            a = crear_alerta_si_corresponde(4, "RPM del motor", "RPM", 2345.0, 73, " rpm")
        self.assertEqual((a.tipo, a.mensaje, a.leida, a.fecha_alerta.microsecond),
                         ("falla", "Falla crítica en RPM del motor: nivel 73% (2345.0 rpm).", 0, 0))

    def test_advertencia_y_nivel_bajo(self):
        a = crear_alerta_si_corresponde(4, "O2", "O2", 0.5, 40, "")
        self.assertEqual((a.tipo, a.mensaje), ("advertencia", "Advertencia en O2: nivel 40% (0.5)."))
        self.assertIsNone(crear_alerta_si_corresponde(4, "O2", "O2", 0.1, 39, ""))
        self.assertEqual(Alerta.objects.count(), 1)
