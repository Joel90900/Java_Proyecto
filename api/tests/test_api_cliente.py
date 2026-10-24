from unittest import mock

from django.test import Client, TestCase

from core.models import Cliente, Sensor, Vehiculo
from core.tests.fabricas import CLAVE, crear_cliente, crear_sensor, crear_vehiculo


def info(c):
    return {"idCliente": c.pk, "nombreCliente": c.nombre_cliente, "apellidoCliente": c.apellido_cliente,
            "correo": c.correo, "estado": c.estado}


class AuthApiTests(TestCase):
    def test_registro(self):
        r = self.client.post("/api/auth/register", {"nombre": " Ana ", "apellido": " Paz ", "correo": " ana@test.com ",
                                                    "contrasena": "secreto1"})
        ana = Cliente.objects.get(correo="ana@test.com")
        self.assertEqual(r.json(), {"ok": True, "mensaje": "Cuenta creada correctamente.", "cliente": info(ana)})
        self.assertEqual(list(r.json()), ["ok", "mensaje", "cliente"])
        self.assertEqual(list(r.json()["cliente"]), ["idCliente", "nombreCliente", "apellidoCliente", "correo", "estado"])
        self.assertEqual(ana.nombre_cliente, "Ana")

    def test_registro_duplicado_y_parametro_faltante(self):
        crear_cliente()
        r = self.client.post("/api/auth/register", {"nombre": "a", "apellido": "b", "correo": "joel@test.com",
                                                    "contrasena": "secreto"})
        self.assertEqual(r.json(), {"ok": False, "mensaje": "El correo ya está registrado."})
        sin_clave = Client(raise_request_exception=False).post("/api/auth/register",
                                                               {"nombre": "a", "apellido": "b", "correo": "z@z.co"})
        self.assertEqual(sin_clave.status_code, 400)

    def test_login(self):
        c = crear_cliente()
        bloqueado = crear_cliente(correo="b@test.com", estado="bloqueado")
        ok = self.client.post("/api/auth/login", {"correo": "joel@test.com", "contrasena": CLAVE})
        self.assertEqual(ok.json(), {"ok": True, "mensaje": "Bienvenido.", "cliente": info(c)})
        self.assertNotIn("cliente_id", self.client.session)
        mal = self.client.post("/api/auth/login", {"correo": "joel@test.com", "contrasena": "mala"})
        self.assertEqual(mal.json(), {"ok": False, "mensaje": "Correo o contraseña incorrectos."})
        b = self.client.post("/api/auth/login", {"correo": bloqueado.correo, "contrasena": CLAVE})
        self.assertEqual(b.json(), {"ok": False, "mensaje": "Tu cuenta está bloqueada. Contacta al administrador."})

    def test_sin_csrf_y_json_utf8_sin_escapar(self):  # F1 + Review Focus 3
        r = Client(enforce_csrf_checks=True).post("/api/auth/login", {"correo": "x@x.co", "contrasena": "y"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("contraseña".encode(), r.content)


class EspaciosFinalesComoMysqlTests(TestCase):  # revisión final #1
    def test_registro_con_espacio_final_detecta_el_duplicado(self):
        crear_cliente()
        r = self.client.post("/api/auth/register", {"nombre": "a", "apellido": "b", "correo": "joel@test.com ",
                                                    "contrasena": "secreto"})
        self.assertEqual(r.json(), {"ok": False, "mensaje": "El correo ya está registrado."})
        self.assertEqual(Cliente.objects.count(), 1)

    def test_login_y_datos_con_espacio_final(self):
        crear_cliente()
        r = self.client.post("/api/auth/login", {"correo": "joel@test.com ", "contrasena": CLAVE})
        self.assertTrue(r.json()["ok"])
        self.assertTrue(self.client.get("/api/cliente/joel@test.com%20").json()["ok"])


class DatosClienteTests(TestCase):
    def test_estructura_completa(self):
        c = crear_cliente()
        v = crear_vehiculo(c, modelo="2018-01-01")
        s = [crear_sensor(v, nivel=n, tipo=t) for n, t in ((10, "MAF"), (50, "O2"), (80, "ECT"))]
        r = self.client.get("/api/cliente/JOEL@test.com")
        self.assertEqual(r.json(), {"ok": True, "cliente": info(c), "vehiculos": [{
            "idVehiculo": v.pk, "nombreVehiculo": "Onix", "marca": "Chevrolet", "modelo": "2018", "color": "Negro",
            "placa": "ABC123", "tipoPlaca": "particular",
            "sensores": [{"idSensor": x.pk, "nombreSensor": x.nombre_sensor, "tipoSensor": x.tipo_sensor,
                          "tipoDano": x.tipo_dano, "nivel": x.nivel} for x in s]}],
            "estadisticas": {"totalVehiculos": 1, "totalSensores": 3, "sensoresOk": 1, "advertencias": 1, "fallas": 1}})

    def test_modelo_vacio_y_cliente_inexistente(self):
        crear_vehiculo(crear_cliente(), modelo=None)
        self.assertEqual(self.client.get("/api/cliente/joel@test.com").json()["vehiculos"][0]["modelo"], "")
        self.assertEqual(self.client.get("/api/cliente/nadie@test.com").json(),
                         {"ok": False, "mensaje": "Cliente no encontrado."})


class CrearVehiculoApiTests(TestCase):
    BASE = {"correo": "joel@test.com", "nombreVehiculo": "Onix", "marca": "Chevrolet", "modelo": " 2020 ",
            "color": "Negro", "placa": " abc123 ", "tipoPlaca": "particular"}

    def setUp(self):
        crear_cliente()

    def test_crea_con_valores_recortados(self):
        r = self.client.post("/api/vehiculos/crear", self.BASE)
        self.assertEqual(r.json(), {"ok": True, "mensaje": "Vehículo registrado correctamente."})
        v = Vehiculo.objects.get()
        self.assertEqual((v.modelo, v.placa, v.sensores.count()), ("2020-01-01", "ABC123", 4))

    def test_mensajes_en_orden(self):
        crear_vehiculo(Cliente.objects.get(), placa="DUP111")
        casos = [({"correo": "nadie@test.com"}, "Cliente no encontrado."),
                 ({"color": " "}, "Todos los campos son obligatorios."),
                 ({"modelo": "1989"}, "El año debe estar entre 1990 y 2030."),
                 ({"modelo": "abc"}, "El año debe ser un número válido."),
                 ({"placa": "dup111"}, "Ya existe un vehículo registrado con esa placa."),
                 ({"placa": "AB1234"}, "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")]
        for cambio, mensaje in casos:
            with self.subTest(cambio):
                self.assertEqual(self.client.post("/api/vehiculos/crear", {**self.BASE, **cambio}).json(),
                                 {"ok": False, "mensaje": mensaje})


class SimularApiTests(TestCase):
    def test_simular_suma_delta_con_limites(self):
        v = crear_vehiculo(crear_cliente())
        alto = crear_sensor(v, nivel=90)
        crear_sensor(v, nivel=3)
        with mock.patch("api.views.random.randint", side_effect=[25, -6]) as azar:
            r = self.client.post("/api/bluetooth/simular", {"correo": "joel@test.com"})
        azar.assert_called_with(-6, 25)
        self.assertEqual([s["nivel"] for s in r.json()["vehiculos"][0]["sensores"]], [100, 0])
        self.assertEqual(Sensor.objects.get(pk=alto.pk).nivel, 100)
        self.assertEqual(self.client.post("/api/bluetooth/simular", {"correo": "x@x.co"}).json(),
                         {"ok": False, "mensaje": "Cliente no encontrado."})


class ApiValidacionesTests(TestCase):  # lote A
    def test_registro_valida_correo_y_contrasena(self):
        for datos, mensaje in (({"correo": "abc", "contrasena": "secreto"}, "El correo no tiene un formato válido."),
                               ({"correo": "a@b.co", "contrasena": "12"}, "La contraseña debe tener al menos 6 caracteres.")):
            r = self.client.post("/api/auth/register", {"nombre": "A", "apellido": "B", **datos})
            self.assertEqual(r.json(), {"ok": False, "mensaje": mensaje})

    def test_tipo_placa_texto_libre_de_la_app(self):  # Review Focus 1
        crear_cliente()
        base = {"correo": "joel@test.com", "nombreVehiculo": "Onix", "marca": "Chevrolet", "modelo": "2020", "color": "Negro"}
        for i, tipo in enumerate(("Público", " PARTICULAR ", "oficial")):
            r = self.client.post("/api/vehiculos/crear", {**base, "placa": f"ABC12{i}", "tipoPlaca": tipo})
            self.assertTrue(r.json()["ok"], tipo)
        self.assertEqual(sorted(Vehiculo.objects.values_list("tipo_placa", flat=True)), ["oficial", "particular", "publico"])
        r = self.client.post("/api/vehiculos/crear", {**base, "placa": "ABC999", "tipoPlaca": "taxi"})
        self.assertEqual(r.json(), {"ok": False, "mensaje": "Selecciona un tipo de placa válido."})
