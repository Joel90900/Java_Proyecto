from types import SimpleNamespace as O

from django.test import SimpleTestCase

from core.templatetags.autosen import estado_informe, estado_nivel, java, multiplicar


class FiltrosPlantillaTests(SimpleTestCase):
    def test_estado_nivel(self):
        self.assertEqual([estado_nivel(n, "F,A,O") for n in (100, 70, 69, 40, 39, None)],
                         ["F", "F", "A", "A", "O", "O"])

    def test_estado_informe(self):
        casos = [(O(nivel=10, estado="FALLA"), "F"), (O(nivel=10, estado="advertencia"), "A"),
                 (O(nivel=None, estado=None), "O"), (O(nivel=75, estado=None), "F"), (O(nivel=45, estado="OK"), "A")]
        for obj, esperado in casos:
            self.assertEqual(estado_informe(obj, "F,A,O"), esperado)

    def test_java_concatena_null_como_en_thymeleaf(self):
        self.assertEqual([java(None), java("x"), java(50)], ["null", "x", "50"])

    def test_multiplicar_como_double_de_java(self):
        self.assertEqual([multiplicar(0, 0.08), multiplicar(1, 0.08), multiplicar(3, 0.08), multiplicar(7, 0.1)],
                         ["0.0", "0.08", "0.24", "0.7000000000000001"])
