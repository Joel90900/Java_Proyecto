import io
from contextlib import redirect_stdout
from importlib import import_module

from django.apps import apps as django_apps
from django.test import TestCase

from core.models import Sensor, Vehiculo
from core.tests.fabricas import crear_cliente, crear_usuario, crear_vehiculo

normalizar_datos = import_module("core.migrations.0002_normalizar_datos").normalizar_datos


class NormalizarDatosTests(TestCase):
    def test_normaliza_vehiculos_existentes(self):
        v = crear_vehiculo(crear_cliente(), placa=" emt262 ", tipo_placa="Público", modelo="2020")
        normalizar_datos(django_apps, None)
        v.refresh_from_db()
        self.assertEqual((v.placa, v.tipo_placa, v.modelo), ("EMT262", "publico", "2020-01-01"))

    def test_quita_el_guion_y_avisa_las_placas_que_chocan(self):  # revisión final
        c = crear_cliente()
        con_guion = crear_vehiculo(c, placa="XYZ-999")
        choque = [crear_vehiculo(c, placa=p) for p in ("ABC-123", "abc123")]
        salida = io.StringIO()
        with redirect_stdout(salida):
            normalizar_datos(django_apps, None)
        self.assertEqual(Vehiculo.objects.get(pk=con_guion.pk).placa, "XYZ999")
        self.assertEqual([Vehiculo.objects.get(pk=v.pk).placa for v in choque], ["ABC-123", "abc123"])
        self.assertIn("ABC123", salida.getvalue())

    def test_la_0004_vuelve_a_normalizar(self):  # bases que ya aplicaron la 0002
        operacion = import_module("core.migrations.0004_placas_sin_guion").Migration.operations[0]
        self.assertIs(operacion.code, normalizar_datos)

    def test_tipo_desconocido_se_conserva(self):  # no inventa datos
        v = crear_vehiculo(crear_cliente(), tipo_placa="Taxi")
        normalizar_datos(django_apps, None)
        v.refresh_from_db()
        self.assertEqual(v.tipo_placa, "Taxi")

    def test_normalizar_datos_es_idempotente(self):  # Review Focus 3
        v = crear_vehiculo(crear_cliente(), placa="ABC123", tipo_placa="particular", modelo="2020-01-01")
        normalizar_datos(django_apps, None)
        normalizar_datos(django_apps, None)
        v.refresh_from_db()
        self.assertEqual((v.placa, v.tipo_placa, v.modelo), ("ABC123", "particular", "2020-01-01"))

    def test_nivel_obligatorio_con_cero_por_defecto(self):
        self.assertFalse(Sensor._meta.get_field("nivel").null)
        sensor = Sensor.objects.create(vehiculo=crear_vehiculo(crear_cliente()), nombre_sensor="S", tipo_sensor="T")
        self.assertEqual(sensor.nivel, 0)

    def test_borrar_admin_desvincula_clientes(self):  # Review Focus 5
        admin = crear_usuario()
        c = crear_cliente()
        c.usuario = admin
        c.save()
        admin.delete()
        c.refresh_from_db()
        self.assertIsNone(c.usuario)
