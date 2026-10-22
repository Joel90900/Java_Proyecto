from django.db import models
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from core.models import Alerta, Cliente, Lectura, Sensor, Usuario, Vehiculo
from core.tests.fabricas import crear_alerta, crear_cliente, crear_lectura, crear_sensor, crear_vehiculo


class EsquemaTests(TestCase):
    def test_nombres_de_tablas(self):
        self.assertEqual([m._meta.db_table for m in (Usuario, Cliente, Vehiculo, Sensor, Lectura, Alerta)],
                         ["usuario", "cliente", "vehiculo", "sensores", "lecturas", "alertas"])

    def test_columnas_conservan_nombres_mysql(self):
        self.assertEqual(Sensor._meta.get_field("tipo_dano").column, "Tipo_daño")
        self.assertEqual(Vehiculo._meta.get_field("cliente").column, "Id_cliente")
        self.assertEqual(Cliente._meta.get_field("usuario").column, "Id_usuario")
        self.assertEqual(Vehiculo._meta.get_field("elm_mac").column, "elm_mac")
        self.assertEqual(Alerta._meta.get_field("fecha_alerta").column, "Fecha_alerta")

    def test_lecturas_y_alertas_sin_clave_foranea(self):  # F3
        for modelo in (Lectura, Alerta):
            campo = modelo._meta.get_field("id_vehiculo")
            self.assertIsInstance(campo, models.IntegerField)
            self.assertFalse(campo.is_relation)
            self.assertTrue(campo.db_index)


class ComportamientoTests(TestCase):
    def test_valores_por_defecto(self):
        c = Cliente.objects.create(nombre_cliente="A", apellido_cliente="B", contrasena="h", correo="a@b.c")
        self.assertEqual(c.estado, "activo")
        v = crear_vehiculo(c)
        s = Sensor.objects.create(vehiculo=v, nombre_sensor="S", tipo_sensor="T")
        self.assertEqual(s.nivel, 0)
        lectura = crear_lectura(v.pk)
        self.assertEqual((lectura.unidad, lectura.estado), ("", "OK"))
        self.assertEqual(crear_alerta(v.pk).leida, 0)

    def test_sensor_sin_tipo_dano(self):  # F4
        s = crear_sensor(crear_vehiculo(crear_cliente()), tipo_dano=None)
        self.assertIsNone(Sensor.objects.get(pk=s.pk).tipo_dano)

    def test_borrar_vehiculo_borra_sensores_y_conserva_historial(self):  # F3
        v = crear_vehiculo(crear_cliente())
        crear_sensor(v)
        crear_lectura(v.pk)
        crear_alerta(v.pk)
        v.delete()
        self.assertEqual((Sensor.objects.count(), Lectura.objects.count(), Alerta.objects.count()), (0, 1, 1))

    def test_cliente_con_vehiculos_esta_protegido(self):
        c = crear_cliente()
        crear_vehiculo(c)
        with self.assertRaises(ProtectedError):
            c.delete()

    def test_related_names_y_orden_por_pk(self):
        c = crear_cliente()
        v2 = crear_vehiculo(c, placa="BBB222")
        v1 = crear_vehiculo(c, placa="AAA111")
        self.assertEqual(list(c.vehiculos.all()), [v2, v1])
        s1 = crear_sensor(v1, nivel=90)
        s2 = crear_sensor(v1, nivel=10)
        self.assertEqual(list(v1.sensores.all()), [s1, s2])
