from types import SimpleNamespace as O

from django.test import SimpleTestCase

from core.templatetags.autosen import estado_informe, estado_nivel


class FiltrosPlantillaTests(SimpleTestCase):
    def test_estado_nivel(self):
        self.assertEqual([estado_nivel(n, "F,A,O") for n in (100, 70, 69, 40, 39, None)],
                         ["F", "F", "A", "A", "O", "O"])

    def test_estado_informe(self):
        casos = [(O(nivel=10, estado="FALLA"), "F"), (O(nivel=10, estado="advertencia"), "A"),
                 (O(nivel=None, estado=None), "O"), (O(nivel=75, estado=None), "F"), (O(nivel=45, estado="OK"), "A")]
        for obj, esperado in casos:
            self.assertEqual(estado_informe(obj, "F,A,O"), esperado)
