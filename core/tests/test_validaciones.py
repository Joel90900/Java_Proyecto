from django.test import SimpleTestCase

from core.validaciones import validar_persona, validar_vehiculo


class ValidarPersonaTests(SimpleTestCase):
    def test_orden_y_mensajes(self):
        self.assertEqual(validar_persona(["Ana", ""], "a@b.co", "secreto"), "Todos los campos son obligatorios.")
        self.assertEqual(validar_persona(["Ana"], "", "secreto"), "Todos los campos son obligatorios.")
        self.assertEqual(validar_persona(["Ana"], "a@b.co", ""), "Todos los campos son obligatorios.")
        for malo in ("abc", "a@b", "a b@c.co", "@b.co"):
            self.assertEqual(validar_persona(["Ana"], malo, "secreto"), "El correo no tiene un formato válido.", malo)
        self.assertEqual(validar_persona(["Ana"], "a@b.co", "12345"), "La contraseña debe tener al menos 6 caracteres.")
        self.assertIsNone(validar_persona(["Ana", "Paz"], "ana@test.com", "secreto"))

    def test_contrasena_opcional(self):
        self.assertIsNone(validar_persona(["Ana"], "a@b.co", "", contrasena_obligatoria=False))
        self.assertIsNone(validar_persona(["Ana"], "a@b.co", None, contrasena_obligatoria=False))
        self.assertEqual(validar_persona(["Ana"], "a@b.co", "123", contrasena_obligatoria=False),
                         "La contraseña debe tener al menos 6 caracteres.")


class ValidarVehiculoTests(SimpleTestCase):
    BASE = dict(nombre="Onix", marca="Chevrolet", modelo="2020", color="Negro", placa="ABC123", tipo_placa="particular")

    def test_orden_y_mensajes(self):
        casos = [({"marca": ""}, "Todos los campos son obligatorios."),
                 ({"modelo": ""}, "Todos los campos son obligatorios."),
                 ({"modelo": "20x0"}, "El año debe ser un número válido."),
                 ({"modelo": "1989"}, "El año debe estar entre 1990 y 2030."),
                 ({"placa": "AB1234"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123."),
                 ({"tipo_placa": "taxi"}, "Selecciona un tipo de placa válido.")]
        for cambio, mensaje in casos:
            self.assertEqual(validar_vehiculo(**{**self.BASE, **cambio}), mensaje, cambio)
        self.assertIsNone(validar_vehiculo(**{**self.BASE, "tipo_placa": "Público", "placa": "ABC-123"}))

    def test_modelo_opcional(self):
        self.assertIsNone(validar_vehiculo(**{**self.BASE, "modelo": None}, modelo_obligatorio=False))
        self.assertEqual(validar_vehiculo(**{**self.BASE, "modelo": "1800"}, modelo_obligatorio=False),
                         "El año debe estar entre 1990 y 2030.")
