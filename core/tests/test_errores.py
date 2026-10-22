from django.test import Client, RequestFactory, TestCase

from core import errores


class PaginasDeErrorTests(TestCase):
    def test_404_en_ruta_publica(self):
        r = Client().get("/api/no-existe")
        self.assertContains(r, "NO ENCONTRADA", status_code=404)
        self.assertContains(r, "Not Found", status_code=404)

    def test_get_error_muestra_500_con_estado_200(self):
        r = Client().get("/error")
        self.assertContains(r, "DEL SERVIDOR")
        self.assertContains(r, "Código: 500")

    def test_handlers_400_y_500(self):
        req = RequestFactory().get("/x")
        self.assertContains(errores.error_400(req, Exception()), "Bad Request", status_code=400)
        self.assertContains(errores.error_500(req), "Internal Server Error", status_code=500)
