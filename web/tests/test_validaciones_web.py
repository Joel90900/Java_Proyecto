from django.test import TestCase

from core.models import Cliente
from core.tests.fabricas import crear_vehiculo
from web.tests.test_vehiculos import DATOS, Base


class TextosLargosWebTests(Base):  # revisión final: antes daban error 500
    def test_textos_largos_muestran_mensaje(self):
        r = self.client.post("/vehiculos/crear", {**DATOS, "color": "Gris oscuro metalizado mate"})
        self.assertContains(r, "El campo color admite como máximo 25 caracteres.")
        v = crear_vehiculo(self.cliente, placa="ABC123")
        r = self.client.post(f"/vehiculos/{v.pk}/editar", {**DATOS, "placa": "ABC123", "marca": "x" * 51})
        self.assertContains(r, "El campo marca admite como máximo 50 caracteres.")
        self.client.post("/logout")
        r = self.client.post("/register", {"nombre": "A", "apellido": "B", "correo": "a@b.co", "contrasena": "x" * 80})
        self.assertContains(r, "La contraseña es demasiado larga.")


class RegistroValidadoTests(TestCase):
    def test_recorta_y_valida(self):
        r = self.client.post("/register", {"nombre": " Ana ", "apellido": " Paz ", "correo": " ana@test.com ",
                                           "contrasena": "secreto"})
        self.assertRedirects(r, "/login", fetch_redirect_response=False)
        self.assertEqual(Cliente.objects.get(correo="ana@test.com").nombre_cliente, "Ana")

    def test_mensajes(self):
        base = {"nombre": "A", "apellido": "B", "correo": "a@b.co", "contrasena": "secreto"}
        for cambio, mensaje in (({"correo": "abc"}, "El correo no tiene un formato válido."),
                                ({"contrasena": "123"}, "La contraseña debe tener al menos 6 caracteres.")):
            self.assertContains(self.client.post("/register", {**base, **cambio}), mensaje)


class VehiculosValidadosTests(Base):
    def test_editar_vehiculo_importado_con_placa_minuscula(self):
        v = crear_vehiculo(self.cliente, placa="emt262", tipo_placa="publico")
        r = self.client.post(f"/vehiculos/{v.pk}/editar", {"nombreVehiculo": "Onix", "marca": "Chevrolet",
                                                           "color": "Negro", "placa": "emt262", "tipoPlaca": "publico"})
        self.assertRedirects(r, "/vehiculos", fetch_redirect_response=False)
        v.refresh_from_db()
        self.assertEqual(v.placa, "EMT262")

    def test_editar_placa_invalida_importada(self):  # Review Focus 2
        v = crear_vehiculo(self.cliente, placa="432fsfdf")
        r = self.client.post(f"/vehiculos/{v.pk}/editar", {"nombreVehiculo": "Onix", "marca": "Chevrolet",
                                                           "color": "Negro", "placa": "432fsfdf", "tipoPlaca": "particular"})
        self.assertContains(r, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")

    def test_tipo_placa_invalido(self):
        self.assertContains(self.client.post("/vehiculos/crear", {**DATOS, "tipoPlaca": "taxi"}),
                            "Selecciona un tipo de placa válido.")

    def test_boton_eliminar(self):
        v = crear_vehiculo(self.cliente)
        r = self.client.get("/vehiculos")
        self.assertContains(r, f'action="/vehiculos/{v.pk}/eliminar"')
        self.assertContains(r, "¿Eliminar este vehículo y sus sensores?")

    def test_login_web_con_espacio_inicial(self):
        self.client.post("/logout")
        r = self.client.post("/login", {"correo": " joel@test.com", "contrasena": "clave123"})
        self.assertRedirects(r, "/dashboard", fetch_redirect_response=False)
