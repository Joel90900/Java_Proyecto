from django.test import TestCase

from core.models import Cliente, Lectura, Usuario, Vehiculo
from core.tests.fabricas import (crear_cliente, crear_lectura, crear_sensor, crear_usuario, crear_vehiculo, login_admin,
                                 login_cliente)


class AccesoTests(TestCase):
    def test_sin_sesion_y_con_sesion_de_cliente(self):  # F2
        self.assertRedirects(self.client.get("/admin"), "/admin/login", fetch_redirect_response=False)
        login_cliente(self.client, crear_cliente())
        for url in ("/admin", "/admin/cliente/nuevo", "/admin/usuario/nuevo"):
            self.assertRedirects(self.client.get(url), "/admin/login", fetch_redirect_response=False)


class Base(TestCase):
    def setUp(self):
        self.admin = crear_usuario()
        login_admin(self.client, self.admin)


class DashboardAdminTests(Base):
    def test_totales_con_nivel_nulo(self):  # Review Focus 2
        v = crear_vehiculo(crear_cliente())
        for n in (10, 45, 75, 0):
            crear_sensor(v, nivel=n)
        r = self.client.get("/admin")
        self.assertEqual([r.context[k] for k in ("totalSensores", "totalFallas", "totalAdvertencias", "sensoresOk",
                                                 "totalClientes")], [4, 1, 1, 2, 1])
        self.assertContains(r, "admin@autosen.com")
        self.assertContains(r, "0%")


class ClientesTests(Base):
    def test_crear_cliente(self):
        r = self.client.post("/admin/cliente/crear", {"nombre": " Ana ", "apellido": "Paz", "correo": " ana@test.com ",
                                                      "contrasena": "secreto"})
        self.assertRedirects(r, "/admin", fetch_redirect_response=False)
        ana = Cliente.objects.get(correo="ana@test.com")
        self.assertEqual((ana.nombre_cliente, ana.estado, ana.contrasena[:7]), ("Ana", "activo", "$2a$10$"))

    def test_validaciones_crear(self):
        crear_cliente()
        base = {"nombre": "A", "apellido": "B", "correo": "a@b.co", "contrasena": "secreto"}
        for cambio, mensaje in (({"nombre": " "}, "Todos los campos son obligatorios."),
                                ({"correo": "abco"}, "El correo no tiene un formato válido."),
                                ({"contrasena": "12345"}, "La contraseña debe tener al menos 6 caracteres."),
                                ({"correo": "JOEL@test.com"}, "Ya existe un cliente con ese correo.")):
            self.assertContains(self.client.post("/admin/cliente/crear", {**base, **cambio}), mensaje)

    def test_editar_cliente(self):
        c = crear_cliente()
        crear_cliente(correo="otro@test.com")
        url = f"/admin/cliente/{c.pk}/editar"
        clave_antes = c.contrasena
        self.client.post(url, {"nombre": "J", "apellido": "M", "correo": "joel@test.com", "contrasena": ""})
        c.refresh_from_db()
        self.assertEqual(c.contrasena, clave_antes)
        self.assertContains(self.client.post(url, {"nombre": "J", "apellido": "M", "correo": "otro@test.com"}),
                            "Ya existe un cliente con ese correo.")
        self.assertContains(self.client.post(url, {"nombre": "J", "apellido": "M", "correo": "joel@test.com",
                                                   "contrasena": "123"}),
                            "La contraseña debe tener al menos 6 caracteres.")

    def test_cambiar_estado(self):
        c = crear_cliente()
        url = f"/admin/cliente/{c.pk}/estado"
        self.client.post(url)
        c.refresh_from_db()
        self.assertEqual(c.estado, "bloqueado")
        self.client.post(url)
        c.refresh_from_db()
        self.assertEqual(c.estado, "activo")
        Cliente.objects.filter(pk=c.pk).update(estado=None)
        self.client.post(url)
        c.refresh_from_db()
        self.assertEqual(c.estado, "activo")

    def test_eliminar_cliente_con_vehiculos_y_lecturas(self):  # F3
        c = crear_cliente()
        v = crear_vehiculo(c)
        crear_sensor(v)
        crear_lectura(v.pk)
        self.assertRedirects(self.client.post(f"/admin/cliente/{c.pk}/eliminar"), "/admin", fetch_redirect_response=False)
        self.assertEqual((Cliente.objects.count(), Vehiculo.objects.count(), Lectura.objects.count()), (0, 0, 1))

    def test_id_inexistente_da_404(self):  # lote A
        for url in ("/admin/cliente/9999/editar", "/admin/vehiculo/9999/editar", "/admin/sensor/9999/editar",
                    "/admin/usuario/9999/editar"):
            self.assertContains(self.client.get(url), "NO ENCONTRADA", status_code=404, msg_prefix=url)
        for url in ("/admin/cliente/9999/estado", "/admin/usuario/9999/eliminar"):
            self.assertEqual(self.client.post(url).status_code, 404, url)


class UsuariosTests(Base):
    def test_crear_con_rol_libre_y_rol_vacio(self):  # S2
        base = {"nombre": "Ana", "contrasena": "secreto"}
        self.client.post("/admin/usuario/crear", {**base, "correo": "ana@autosen.com", "rol": "SUPERADMIN"})
        self.client.post("/admin/usuario/crear", {**base, "correo": "eva@autosen.com", "rol": " "})
        self.assertEqual([u.rol for u in Usuario.objects.exclude(pk=self.admin.pk)], ["SUPERADMIN", "ADMIN"])
        self.assertContains(self.client.post("/admin/usuario/crear", {**base, "correo": "ADMIN@autosen.com", "rol": "ADMIN"}),
                            "Ya existe un usuario con ese correo.")

    def test_editar_rol_vacio_conserva(self):
        self.client.post(f"/admin/usuario/{self.admin.pk}/editar", {"nombre": "Jefe", "correo": "admin@autosen.com",
                                                                    "rol": ""})
        self.admin.refresh_from_db()
        self.assertEqual((self.admin.nombre, self.admin.rol), ("Jefe", "admin"))

    def test_eliminar(self):
        self.client.post(f"/admin/usuario/{self.admin.pk}/eliminar")  # a sí mismo: no
        self.assertEqual(Usuario.objects.count(), 1)
        otro = crear_usuario(correo="otro@autosen.com")
        self.client.post(f"/admin/usuario/{otro.pk}/eliminar")
        self.assertFalse(Usuario.objects.filter(pk=otro.pk).exists())
