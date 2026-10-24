from django.test import TestCase

from core.tests.fabricas import crear_cliente, crear_sensor, crear_vehiculo
from reportes.filtros import filtrar_clientes, filtrar_sensores, normalizar_rango, ordenar_sensores


def datos_reportes():
    """Datos compartidos por las pruebas de reportes y exportaciones."""
    joel = crear_cliente(correo="joel@test.com", nombre="Joel", apellido="Moncaleano")
    ana = crear_cliente(correo="ana@test.com", nombre="Ana", apellido="Paz", estado="bloqueado")
    v1 = crear_vehiculo(joel, placa="EMT262", marca="Chevrolet", tipo_placa="Público")
    v2 = crear_vehiculo(ana, placa="KIA111", nombre="Rio", marca="Kia", tipo_placa="particular")
    s1 = crear_sensor(v1, nivel=10, tipo="MAF", nombre="Sensor MAF")
    s2 = crear_sensor(v1, nivel=50, tipo="O2", nombre="Sensor O2")
    s3 = crear_sensor(v2, nivel=80, tipo="ECT", nombre="Sensor ECT", tipo_dano=None)
    s4 = crear_sensor(v2, nivel=0, tipo="TEST", nombre="Prueba")
    return joel, ana, (s1, s2, s3, s4)


class FiltrosTests(TestCase):
    def setUp(self):
        self.joel, self.ana, (self.s1, self.s2, self.s3, self.s4) = datos_reportes()
        self.sensores = [self.s1, self.s2, self.s3, self.s4]
        self.clientes = [self.joel, self.ana]

    def test_filtrar_sensores(self):
        def f(*a):
            return filtrar_sensores(self.sensores, *a)
        self.assertEqual(f("falla", None, None, None), [self.s3])
        self.assertEqual(f("OPTIMO", None, None, None), [self.s1, self.s4])
        self.assertEqual((f(None, "O2", None, None), f(None, "o2", None, None)), ([self.s2], []))
        self.assertEqual(f(None, None, 40, None), [self.s2, self.s3])
        self.assertEqual(f(None, None, None, 50), [self.s1, self.s2, self.s4])

    def test_filtrar_clientes(self):
        def f(*a):
            return filtrar_clientes(self.clientes, *a)
        self.assertEqual([f("emt", None, None, None), f("PAZ", None, None, None), f(None, "BLOQUEADO", None, None),
                          f(None, None, "kia", None)], [[self.joel], [self.ana], [self.ana], [self.ana]])

    def test_buscar_placa_con_guion(self):  # revisión final: las placas se guardan sin guion
        self.assertEqual(filtrar_clientes(self.clientes, "emt-262", None, None, None), [self.joel])

    def test_tipo_placa_sin_tildes(self):  # F5 + Review Focus 1
        self.assertEqual(filtrar_clientes(self.clientes, None, None, None, "publico"), [self.joel])
        self.assertEqual(filtrar_clientes(self.clientes, None, None, None, "PARTICULAR"), [self.ana])

    def test_ordenar_y_rango(self):
        self.assertEqual(ordenar_sensores(self.sensores, "nivel"), [self.s3, self.s2, self.s1, self.s4])
        self.assertEqual(ordenar_sensores(self.sensores, "estado"), [self.s1, self.s4, self.s2, self.s3])
        self.assertEqual(ordenar_sensores(self.sensores, None), [self.s3, self.s4, self.s1, self.s2])
        self.assertEqual(normalizar_rango(70, 10), (10, 70))
