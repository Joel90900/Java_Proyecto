from django.test import TestCase

from core.consultas import igual_mysql
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
