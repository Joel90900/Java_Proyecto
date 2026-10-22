from django.core.exceptions import BadRequest
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from core.http import metodos, parametro

rf = RequestFactory()


class ParametroTests(SimpleTestCase):
    def test_lee_formulario_y_query(self):
        req = rf.post("/x?b=2", {"a": " 1 "})
        self.assertEqual((parametro(req, "a"), parametro(req, "b")), (" 1 ", "2"))

    def test_texto_vacio_es_valido(self):
        self.assertEqual(parametro(rf.post("/x", {"a": ""}), "a"), "")

    def test_ausente(self):
        with self.assertRaises(BadRequest):
            parametro(rf.post("/x"), "a")
        self.assertIsNone(parametro(rf.get("/x"), "a", requerido=False))

    def test_numeros(self):
        self.assertEqual(parametro(rf.get("/x?n=12"), "n", int), 12)
        self.assertEqual(parametro(rf.get("/x?n=2.5"), "n", float), 2.5)
        self.assertIsNone(parametro(rf.get("/x?n="), "n", int, requerido=False))
        for url, tipo in (("/x?n=", int), ("/x?n=abc", int), ("/x?n=abc", float)):
            with self.assertRaises(BadRequest):
                parametro(rf.get(url), "n", tipo)


class MetodosTests(SimpleTestCase):
    def test_rechaza_metodo_no_permitido_con_405(self):
        vista = metodos("GET")(lambda request: HttpResponse("ok"))
        self.assertEqual(vista(rf.head("/x")).status_code, 200)
        r = vista(rf.post("/x"))
        self.assertEqual(r.status_code, 405)
        self.assertContains(r, "Código: 405", status_code=405)
