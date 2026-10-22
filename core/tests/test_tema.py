from django.http import HttpResponse, JsonResponse
from django.test import Client, RequestFactory, SimpleTestCase

from core.middleware import SNIPPET, TemaMiddleware


def procesar(respuesta):
    return TemaMiddleware(lambda request: respuesta)(RequestFactory().get("/"))


class TemaMiddlewareTests(SimpleTestCase):
    def test_inyecta_antes_de_body(self):
        r = procesar(HttpResponse("<html><body>Hola</body></html>"))
        self.assertEqual(r.content.decode(), "<html><body>Hola" + SNIPPET + "</html>")
        self.assertIn('href="/static/css/light-mode.css"', SNIPPET)
        self.assertIn('src="/static/js/theme-toggle.js"', SNIPPET)
        self.assertEqual(r["Content-Length"], str(len(r.content)))

    def test_reemplaza_todas_las_apariciones(self):
        r = procesar(HttpResponse("<body>a</body><body>b</body>"))
        self.assertEqual(r.content.decode().count("theme-toggle.js"), 2)

    def test_no_toca_lo_que_no_corresponde(self):
        for respuesta in (HttpResponse("<p>sin cierre</p>"),
                          HttpResponse('<body><script src="/static/js/theme-toggle.js"></script></body>'),
                          JsonResponse({"html": "</body>"})):
            antes = respuesta.content
            self.assertEqual(procesar(respuesta).content, antes)

    def test_estaticos_servidos(self):
        self.assertEqual(Client().get("/static/js/theme-toggle.js").status_code, 200)
