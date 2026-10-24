from django.test import Client, TestCase

from core.models import Lectura, Sensor, Vehiculo
from core.tests.fabricas import crear_cliente, crear_lectura, crear_sensor, crear_usuario, crear_vehiculo, login_admin


class Base(TestCase):
    def setUp(self):
        login_admin(self.client, crear_usuario())
        self.cliente = crear_cliente()


class VehiculosAdminTests(Base):
    def datos(self, **cambios):
        return {"clienteId": self.cliente.pk, "nombreVehiculo": " Onix ", "marca": "Chevrolet", "modelo": "2020",
                "color": "Negro", "placa": " abc-123 ", "tipoPlaca": "particular", "elmMac": "", **cambios}

    def test_crear_sin_sensores_por_defecto(self):
        self.assertRedirects(self.client.post("/admin/vehiculo/crear", self.datos()), "/admin",
                             fetch_redirect_response=False)
        v = Vehiculo.objects.get()
        self.assertEqual((v.nombre_vehiculo, v.modelo, v.placa, v.elm_mac, v.sensores.count()),
                         ("Onix", "2020-01-01", "ABC-123", None, 0))

    def test_validaciones_en_orden(self):
        crear_vehiculo(self.cliente, placa="DUP111")
        for cambio, mensaje in (({"marca": " "}, "Todos los campos son obligatorios."),
                                ({"modelo": ""}, "Todos los campos son obligatorios."),
                                ({"tipoPlaca": "taxi"}, "Selecciona un tipo de placa válido."),
                                ({"placa": "AB123"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123."),
                                ({"placa": "dup111"}, "Ya existe un vehículo registrado con esa placa."),
                                ({"clienteId": 9999}, "Selecciona un cliente válido.")):
            self.assertContains(self.client.post("/admin/vehiculo/crear", self.datos(**cambio)), mensaje)
        c = Client(raise_request_exception=False)
        login_admin(c, crear_usuario(correo="b@autosen.com"))
        self.assertEqual(c.post("/admin/vehiculo/crear", self.datos(clienteId="")).status_code, 400)

    def test_editar(self):
        v = crear_vehiculo(self.cliente, modelo="2019-01-01", elm_mac="AA:BB")
        otro = crear_cliente(correo="otro@test.com")
        self.client.post(f"/admin/vehiculo/{v.pk}/editar", self.datos(clienteId=otro.pk, modelo=""))
        v.refresh_from_db()
        self.assertEqual((v.modelo, v.elm_mac, v.cliente), ("2019-01-01", None, otro))
        self.client.post(f"/admin/vehiculo/{v.pk}/editar", self.datos(clienteId=""))
        v.refresh_from_db()
        self.assertEqual(v.cliente, otro)

    def test_editar_muestra_solo_el_anio_y_lo_acepta_de_vuelta(self):
        v = crear_vehiculo(self.cliente, modelo="2019-01-01")
        self.assertContains(self.client.get(f"/admin/vehiculo/{v.pk}/editar"), 'name="modelo" value="2019"')
        self.assertRedirects(self.client.post(f"/admin/vehiculo/{v.pk}/editar", self.datos(modelo="2019")), "/admin",
                             fetch_redirect_response=False)
        v.refresh_from_db()
        self.assertEqual(v.modelo, "2019-01-01")

    def test_editar_tipo_importado_se_preselecciona(self):
        v = crear_vehiculo(self.cliente, tipo_placa="oficial")
        self.assertContains(self.client.get(f"/admin/vehiculo/{v.pk}/editar"), '<option value="oficial" selected')

    def test_crear_cliente_y_usuario_validan_formato(self):
        self.assertContains(self.client.post("/admin/cliente/crear", {"nombre": "A", "apellido": "B", "correo": "a@b",
                                                                      "contrasena": "secreto"}),
                            "El correo no tiene un formato válido.")
        self.assertContains(self.client.post("/admin/usuario/crear", {"nombre": "A", "correo": "a b@c.co",
                                                                      "contrasena": "secreto", "rol": "ADMIN"}),
                            "El correo no tiene un formato válido.")

    def test_eliminar_con_lecturas(self):  # F3
        v = crear_vehiculo(self.cliente)
        crear_sensor(v)
        crear_lectura(v.pk)
        self.client.post(f"/admin/vehiculo/{v.pk}/eliminar")
        self.assertEqual((Vehiculo.objects.count(), Sensor.objects.count(), Lectura.objects.count()), (0, 0, 1))


class FormulariosTests(Base):
    def test_formularios_se_muestran_con_sus_datos(self):
        v = crear_vehiculo(self.cliente, placa="EMT262", elm_mac=None, modelo=None)
        s = crear_sensor(v, nivel=0, tipo_dano=None)
        paginas = {"/admin/cliente/nuevo": "Nuevo cliente", "/admin/usuario/nuevo": "Nuevo administrador",
                   "/admin/vehiculo/nuevo": "Joel Moncaleano", "/admin/sensor/nuevo": "Onix - EMT262 (Joel)",
                   f"/admin/cliente/{self.cliente.pk}/editar": 'value="Joel"',
                   f"/admin/vehiculo/{v.pk}/editar": 'value="EMT262"',
                   f"/admin/sensor/{s.pk}/editar": "Onix - EMT262 (Joel)</option>",
                   "/admin": f'href="/admin/vehiculo/{v.pk}/editar"'}
        for url, texto in paginas.items():
            self.assertContains(self.client.get(url), texto, msg_prefix=url)
        self.assertNotContains(self.client.get(f"/admin/vehiculo/{v.pk}/editar"), "None")


class SensoresAdminTests(Base):
    def setUp(self):
        super().setUp()
        self.v = crear_vehiculo(self.cliente)

    def datos(self, **cambios):
        return {"vehiculoId": self.v.pk, "nombreSensor": " Frenos ", "tipoSensor": "Pastillas", "nivel": "75",
                "tipoDano": "", **cambios}

    def test_crear_con_estado_y_sin_tipo_dano(self):  # F4
        for nivel in ("75", "45", "10"):
            self.client.post("/admin/sensor/crear", self.datos(nivel=nivel))
        self.assertEqual([(s.nombre_sensor, s.estado, s.tipo_dano) for s in Sensor.objects.all()],
                         [("Frenos", "FALLA", None), ("Frenos", "ADVERTENCIA", None), ("Frenos", "OK", None)])

    def test_validaciones(self):
        for cambio, mensaje in (({"nombreSensor": " "}, "Todos los campos obligatorios deben estar completos."),
                                ({"nivel": "101"}, "El nivel debe estar entre 0 y 100."),
                                ({"vehiculoId": 9999}, "Selecciona un vehículo válido.")):
            self.assertContains(self.client.post("/admin/sensor/crear", self.datos(**cambio)), mensaje)

    def test_editar_y_eliminar(self):
        s = crear_sensor(self.v, nivel=10)
        self.client.post(f"/admin/sensor/{s.pk}/editar", self.datos(nivel="70", tipoDano="Desgaste"))
        s.refresh_from_db()
        self.assertEqual((s.nivel, s.estado, s.tipo_dano), (70, "FALLA", "Desgaste"))
        self.client.post(f"/admin/sensor/{s.pk}/eliminar")
        self.assertEqual(Sensor.objects.count(), 0)
