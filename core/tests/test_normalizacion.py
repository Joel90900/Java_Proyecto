from django.test import SimpleTestCase

from core.normalizacion import TIPOS_PLACA, normalizar_modelo, normalizar_placa, normalizar_tipo_placa, sin_tildes


class NormalizacionTests(SimpleTestCase):
    def test_placa(self):
        self.assertEqual([normalizar_placa(p) for p in (" emt262 ", "ABC-123", None)], ["EMT262", "ABC-123", None])

    def test_tipo_placa(self):
        casos = {"Público": "publico", " PARTICULAR ": "particular", "oficial": "oficial", "Diplomático": "diplomatico",
                 "taxi": None, "": None, None: None}
        for valor, esperado in casos.items():
            self.assertEqual(normalizar_tipo_placa(valor), esperado, valor)
        self.assertEqual(TIPOS_PLACA, ("particular", "publico", "oficial", "diplomatico"))

    def test_modelo(self):
        self.assertEqual([normalizar_modelo(m) for m in ("2020", "2018-01-01", "abc", None)],
                         ["2020-01-01", "2018-01-01", "abc", None])

    def test_sin_tildes(self):
        self.assertEqual(sin_tildes("Público"), "publico")
