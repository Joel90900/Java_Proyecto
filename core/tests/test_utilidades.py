from datetime import datetime

from django.test import SimpleTestCase

from core.utilidades import ahora, double_java, entero_java, fecha_java, redondear_java, texto_java


class UtilidadesJavaTests(SimpleTestCase):
    def test_redondear_java_es_mitad_hacia_arriba(self):
        self.assertEqual([redondear_java(x) for x in (2.5, 0.5, -0.5, 22.5, 1.4999)], [3, 1, 0, 23, 1])

    def test_entero_java(self):
        self.assertEqual(entero_java("2020"), 2020)
        self.assertEqual(entero_java("+2020"), 2020)
        self.assertEqual(entero_java("-5"), -5)
        for invalido in (" 2020", "2020 ", "20.5", "", "abc", "2_020"):
            self.assertIsNone(entero_java(invalido), invalido)

    def test_texto_java(self):
        self.assertEqual([texto_java(None), texto_java("x"), texto_java(5)], ["null", "x", "5"])

    def test_double_java(self):
        casos = {95.0: "95.0", 2345.0: "2345.0", 0.12: "0.12", 0.0: "0.0", -3.5: "-3.5",
                 0.0005: "5.0E-4", 12345678.0: "1.2345678E7", 0.001: "0.001"}
        for valor, esperado in casos.items():
            self.assertEqual(double_java(valor), esperado)

    def test_fecha_java(self):
        self.assertEqual(fecha_java(datetime(2026, 10, 21, 19, 45, 12)), "2026-10-21T19:45:12")
        self.assertEqual(fecha_java(datetime(2026, 10, 21, 19, 45, 0)), "2026-10-21T19:45")
        self.assertEqual(fecha_java(None), "null")

    def test_ahora_sin_microsegundos(self):
        self.assertEqual(ahora().microsecond, 0)
