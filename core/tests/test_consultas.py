from django.test import TestCase

from core.consultas import igual_mysql, placa_duplicada
from core.models import Cliente, Vehiculo
from core.tests.fabricas import crear_cliente, crear_vehiculo


class IgualMysqlTests(TestCase):
    """utf8mb4_general_ci de MySQL: ignora mayúsculas y los espacios al final (PAD SPACE), no los del inicio."""

    def test_ignora_mayusculas_y_espacios_finales_del_valor_buscado(self):
        c = crear_cliente(correo="joel@test.com")
        self.assertEqual(igual_mysql(Cliente.objects.all(), "correo", "JOEL@test.com  ").first(), c)

    def test_ignora_espacios_finales_guardados(self):
        c = crear_cliente(correo="ana@test.com  ")
        self.assertEqual(igual_mysql(Cliente.objects.all(), "correo", "ana@test.com").first(), c)

    def test_los_espacios_iniciales_si_cuentan(self):
        crear_cliente(correo="joel@test.com")
        self.assertFalse(igual_mysql(Cliente.objects.all(), "correo", " joel@test.com").exists())

    def test_sirve_para_placas(self):
        v = crear_vehiculo(crear_cliente(), placa="emt262")
        self.assertEqual(igual_mysql(Vehiculo.objects.all(), "placa", "EMT262 ").first(), v)


class PlacaDuplicadaTests(TestCase):  # revisión final
    def test_al_editar_sin_cambiar_la_placa_no_compara(self):
        c = crear_cliente()
        propio = crear_vehiculo(c, placa="abc123")
        crear_vehiculo(c, placa="ABC123")  # quedaron iguales tras normalizar los datos
        self.assertFalse(placa_duplicada("ABC123", propio))
        self.assertTrue(placa_duplicada("ABC123"))
        otro = crear_vehiculo(c, placa="XYZ999")
        self.assertTrue(placa_duplicada("ABC123", otro))
        self.assertFalse(placa_duplicada("XYZ999 ", otro))
