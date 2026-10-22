from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from core.auth import admin_requerido, cliente_requerido
from core.tests.fabricas import crear_cliente, crear_usuario


def peticion(**sesion):
    req = RequestFactory().get("/x")
    req.session = SessionStore()
    req.session.update(sesion)
    return req


def ok(request):
    return HttpResponse("ok")


class DecoradoresTests(TestCase):
    def test_admin_requerido_rechaza_sesion_de_cliente(self):  # F2
        r = admin_requerido(ok)(peticion(cliente_id=crear_cliente().pk))
        self.assertEqual((r.status_code, r["Location"]), (302, "/admin/login"))

    def test_admin_requerido_acepta_admin(self):
        u = crear_usuario()
        req = peticion(admin_id=u.pk)
        self.assertEqual(admin_requerido(ok)(req).status_code, 200)
        self.assertEqual(req.admin_correo, "admin@autosen.com")

    def test_cliente_requerido(self):
        c = crear_cliente()
        self.assertEqual(cliente_requerido(ok)(peticion(admin_id=crear_usuario().pk))["Location"], "/login")
        req = peticion(cliente_id=c.pk)
        self.assertEqual(cliente_requerido(ok)(req).status_code, 200)
        self.assertEqual((req.cliente, req.cliente_correo), (c, "joel@test.com"))

    def test_id_de_sesion_inexistente_redirige(self):
        self.assertEqual(cliente_requerido(ok)(peticion(cliente_id=9999))["Location"], "/login")
