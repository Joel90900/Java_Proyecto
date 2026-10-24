from django.test import TestCase

from core.models import Lectura, Sensor, Vehiculo
from core.tests.fabricas import crear_alerta, crear_cliente, crear_lectura, crear_sensor, crear_vehiculo, login_cliente

DATOS = {"nombreVehiculo": "Onix", "marca": "Chevrolet", "modelo": "2020", "color": "Negro", "placa": "abc-123",
         "tipoPlaca": "particular"}


class Base(TestCase):
    def setUp(self):
        self.cliente = crear_cliente()
        login_cliente(self.client, self.cliente)


class DashboardTests(Base):
    def test_kpis(self):
        v = crear_vehiculo(self.cliente)
        for n in (10, 39, 40, 69, 70):
            crear_sensor(v, nivel=n)
        crear_sensor(crear_vehiculo(crear_cliente(correo="otro@test.com"), placa="ZZZ999"), nivel=90)
        r = self.client.get("/dashboard")
        self.assertTemplateUsed(r, "paginas/dashboard.html")
        self.assertEqual([r.context[k] for k in ("totalSensores", "sensoresOk", "advertencias", "fallas")], [5, 2, 2, 1])
        self.assertRegex(r.content.decode(), r"(lunes|martes|miércoles|jueves|viernes|sábado|domingo), \d{2} \w+ \d{4}")

    def test_id_inexistente_web_da_404(self):  # lote A
        self.assertEqual(self.client.get("/vehiculos/9999/editar").status_code, 404)
        self.assertEqual(self.client.post("/vehiculos/9999/eliminar").status_code, 404)

    def test_sin_sesion(self):
        self.client.post("/logout")
        for url in ("/dashboard", "/vehiculos", "/sensores", "/vehiculos/crear"):
            self.assertRedirects(self.client.get(url), "/login", fetch_redirect_response=False)


class CrearVehiculoTests(Base):
    def test_crea_con_los_cuatro_sensores(self):
        self.assertRedirects(self.client.post("/vehiculos/crear", DATOS), "/vehiculos", fetch_redirect_response=False)
        v = Vehiculo.objects.get()
        self.assertEqual((v.placa, v.modelo, v.cliente), ("ABC-123", "2020-01-01", self.cliente))
        self.assertEqual([(s.tipo_sensor, s.nombre_sensor, s.tipo_dano, s.nivel) for s in v.sensores.all()], [
            ("MAF", "Sensor de Flujo de Masa de Aire (MAF)", "Falla en flujo de aire", 0),
            ("O2", "Sensor de Oxígeno (O2)", "Falla en mezcla", 0),
            ("ECT", "Sensor de Temperatura del Refrigerante (ECT)", "Sobrecalentamiento", 0),
            ("MAP", "Sensor de Presión Absoluta del Colector (MAP)", "Falla en presión", 0)])

    def test_validaciones_en_orden(self):
        crear_vehiculo(self.cliente, placa="xyz")  # placa no válida, como las importadas
        casos = [({"marca": "  "}, "Todos los campos son obligatorios."),
                 ({"modelo": "1989"}, "El año debe estar entre 1990 y 2030."),
                 ({"modelo": "dos mil"}, "El año debe ser un número válido."),
                 ({"placa": "XYZ"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123."),  # formato antes que duplicado
                 ({"placa": "AB1234"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")]
        for cambio, mensaje in casos:
            with self.subTest(cambio):
                self.assertContains(self.client.post("/vehiculos/crear", {**DATOS, **cambio}), mensaje)
        self.assertEqual(Vehiculo.objects.count(), 1)


class PlacaConEspacioFinalTests(Base):  # revisión final #1
    def test_placa_con_espacio_final_es_duplicado_como_en_mysql(self):
        crear_vehiculo(self.cliente, placa="ABC123")
        r = self.client.post("/vehiculos/crear", {**DATOS, "placa": "abc123 "})
        self.assertContains(r, "Ya existe un vehículo registrado con esa placa.")

    def test_login_web_con_espacio_final(self):
        self.client.post("/logout")
        r = self.client.post("/login", {"correo": "joel@test.com ", "contrasena": "clave123"})
        self.assertRedirects(r, "/dashboard", fetch_redirect_response=False)


class EditarEliminarTests(Base):
    def setUp(self):
        super().setUp()
        self.v = crear_vehiculo(self.cliente, placa="ABC123")
        self.ajeno = crear_vehiculo(crear_cliente(correo="otro@test.com"), placa="OTR111")

    def test_vehiculo_ajeno_redirige_sin_cambios(self):
        url = f"/vehiculos/{self.ajeno.pk}"
        self.assertRedirects(self.client.get(url + "/editar"), "/vehiculos", fetch_redirect_response=False)
        self.client.post(url + "/editar", {**DATOS, "placa": "NEW111"})
        self.client.post(url + "/eliminar")
        self.ajeno.refresh_from_db()
        self.assertEqual(self.ajeno.placa, "OTR111")

    def test_editar(self):
        datos = {"nombreVehiculo": "Nuevo", "marca": "Kia", "color": "Azul", "placa": "xyz999", "tipoPlaca": "publico"}
        self.assertRedirects(self.client.post(f"/vehiculos/{self.v.pk}/editar", datos), "/vehiculos",
                             fetch_redirect_response=False)
        self.v.refresh_from_db()
        self.assertEqual((self.v.placa, self.v.marca, self.v.tipo_placa), ("XYZ999", "Kia", "publico"))

    def test_editar_errores(self):
        base = {"nombreVehiculo": "N", "marca": "K", "color": "A", "tipoPlaca": "publico"}
        self.assertContains(self.client.post(f"/vehiculos/{self.v.pk}/editar", {**base, "placa": "otr111"}),
                            "Ya existe un vehículo registrado con esa placa.")
        self.assertContains(self.client.post(f"/vehiculos/{self.v.pk}/editar", {**base, "placa": " "}),
                            "Todos los campos son obligatorios.")
        r = self.client.post(f"/vehiculos/{self.v.pk}/editar", {**base, "placa": "abc123"})  # su propia placa en minúsculas
        self.assertEqual(r.status_code, 302)

    def test_eliminar_conserva_historial(self):  # F3
        crear_sensor(self.v)
        crear_lectura(self.v.pk)
        crear_alerta(self.v.pk)
        self.assertRedirects(self.client.post(f"/vehiculos/{self.v.pk}/eliminar"), "/vehiculos",
                             fetch_redirect_response=False)
        self.assertFalse(Vehiculo.objects.filter(pk=self.v.pk).exists())
        self.assertEqual((Sensor.objects.count(), Lectura.objects.count()), (0, 1))

    def test_paginas_con_datos_importados(self):  # Review Focus 1
        importado = crear_vehiculo(self.cliente, placa="emt262", tipo_placa="Público", modelo="2026-01-01")
        crear_sensor(importado, nivel=50)
        self.assertContains(self.client.get("/vehiculos"), "emt262")
        r = self.client.get("/sensores")
        self.assertContains(r, "ADVERTENCIA")
        self.assertContains(self.client.get(f"/vehiculos/{importado.pk}/editar"), 'value="emt262"')
