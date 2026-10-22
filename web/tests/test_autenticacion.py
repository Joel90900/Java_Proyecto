from django.test import Client, TestCase

from core.models import Cliente
from core.tests.fabricas import CLAVE, crear_cliente, crear_usuario, login_admin, login_cliente


class LoginClienteTests(TestCase):
    def setUp(self):
        self.cliente = crear_cliente()

    def post_login(self, correo, contrasena=CLAVE):
        return self.client.post("/login", {"correo": correo, "contrasena": contrasena})

    def test_login_correcto(self):
        self.assertRedirects(self.post_login("joel@test.com"), "/dashboard", fetch_redirect_response=False)
        self.assertEqual(self.client.session["cliente_id"], self.cliente.pk)

    def test_correo_con_otras_mayusculas(self):
        self.assertRedirects(self.post_login("JOEL@Test.com"), "/dashboard", fetch_redirect_response=False)

    def test_fallos_redirigen_con_error(self):
        Cliente.objects.create(nombre_cliente="B", apellido_cliente="B", correo="b@test.com",
                               contrasena=self.cliente.contrasena, estado="bloqueado")
        for correo, clave in (("joel@test.com", "mala"), ("nadie@test.com", CLAVE), ("b@test.com", CLAVE)):
            self.assertRedirects(self.post_login(correo, clave), "/login?error", fetch_redirect_response=False)

    def test_pagina_login_muestra_error(self):
        self.assertContains(self.client.get("/login?error"), "Correo o contraseña incorrectos.")

    def test_logout_por_get_y_post(self):
        for metodo in ("get", "post"):
            login_cliente(self.client, self.cliente)
            self.assertRedirects(getattr(self.client, metodo)("/logout"), "/login", fetch_redirect_response=False)
            self.assertNotIn("cliente_id", self.client.session)

    def test_paginas_publicas(self):
        for url in ("/", "/nosotros", "/login", "/register", "/admin/login"):
            self.assertEqual(Client().get(url).status_code, 200, url)


class RegistroTests(TestCase):
    def test_registro_sin_recortar_espacios(self):
        r = self.client.post("/register", {"nombre": " Ana ", "apellido": "Paz", "correo": "ana@test.com",
                                           "contrasena": "secreto"})
        self.assertRedirects(r, "/login", fetch_redirect_response=False)
        ana = Cliente.objects.get(correo="ana@test.com")
        self.assertEqual((ana.nombre_cliente, ana.estado), (" Ana ", "activo"))
        self.assertTrue(ana.contrasena.startswith("$2a$10$"))

    def test_registro_correo_duplicado(self):
        crear_cliente()
        r = self.client.post("/register", {"nombre": "J", "apellido": "M", "correo": "JOEL@TEST.COM", "contrasena": "x"})
        self.assertContains(r, "El correo ya está registrado.")


class LoginAdminTests(TestCase):
    def test_login_y_logout_admin(self):
        u = crear_usuario()
        r = self.client.post("/admin/login", {"correo": "admin@autosen.com", "contrasena": CLAVE})
        self.assertRedirects(r, "/admin", fetch_redirect_response=False)
        self.assertEqual(self.client.session["admin_id"], u.pk)
        self.assertRedirects(self.client.post("/admin/logout"), "/admin/login", fetch_redirect_response=False)

    def test_login_admin_fallido(self):
        crear_usuario()
        r = self.client.post("/admin/login", {"correo": "admin@autosen.com", "contrasena": "mala"})
        self.assertRedirects(r, "/admin/login?error", fetch_redirect_response=False)
        self.assertContains(self.client.get("/admin/login?error"), "Credenciales incorrectas.")

    def test_sesiones_independientes(self):  # F2
        login_admin(self.client, crear_usuario())
        login_cliente(self.client, crear_cliente())
        self.client.post("/logout")
        self.assertIn("admin_id", self.client.session)


class RutasDesconocidasTests(TestCase):
    def test_sin_sesion_redirigen_al_login_que_corresponde(self):
        c = Client(raise_request_exception=False)
        self.assertRedirects(c.get("/no-existe"), "/login", fetch_redirect_response=False)
        self.assertRedirects(c.get("/admin/no-existe"), "/admin/login", fetch_redirect_response=False)
        self.assertEqual(c.get("/api/no-existe").status_code, 404)

    def test_con_sesion_dan_404(self):
        login_cliente(self.client, crear_cliente())
        self.assertEqual(self.client.get("/no-existe").status_code, 404)
