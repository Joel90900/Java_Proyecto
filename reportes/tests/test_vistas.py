from django.test import Client, TestCase

from core.tests.fabricas import crear_usuario, login_admin
from reportes.tests.test_filtros import datos_reportes


class VistasReportesTests(TestCase):
    def setUp(self):
        login_admin(self.client, crear_usuario())
        self.joel, self.ana, self.sensores = datos_reportes()

    def test_reportes(self):
        r = self.client.get("/admin/reportes")
        self.assertEqual((r.context["tiposSensor"], r.context["marcas"], r.context["tiposPlaca"]),
                         (["ECT", "MAF", "O2", "TEST"], ["Chevrolet", "Kia"], ["particular", "publico"]))
        self.assertEqual((r.context["totalFallas"], r.context["totalAdvertencias"]), (1, 1))
        self.assertEqual([v.placa for v in r.context["vehiculosConFallas"]], ["KIA111"])

    def test_numeros_vacios_son_sin_filtro(self):  # Review Focus 4 + F5
        r = self.client.get("/admin/reportes-filtrado?tipoPlaca=publico&nivelMin=&nivelMax=")
        self.assertEqual((r.status_code, r.context["clientes"], r.context["nivelMin"]), (200, [self.joel], None))
        self.assertEqual(r.context["tiposSensor"], ["MAF", "O2", "ECT", "TEST"])
        self.assertEqual(len(r.context["todosSensores"]), 4)

    def test_rango_invertido(self):
        r = self.client.get("/admin/reportes-filtrado?nivelMin=70&nivelMax=10")
        self.assertEqual((r.context["nivelMin"], r.context["nivelMax"]), (10, 70))

    def test_informes_imprimibles(self):
        r = self.client.get("/admin/reportes-pdf")
        self.assertEqual([r.context[k] for k in ("saludFlota", "sensoresOptimos", "sensoresAdvertencia", "sensoresFalla")],
                         [50, 2, 1, 1])
        self.assertEqual(len(r.context["alertas"]), 2)
        self.assertTrue(r.context["reporteId"].startswith("RPT-"))
        self.assertContains(self.client.get(f"/admin/reporte-cliente-pdf/{self.joel.pk}"), "EMT262")
        self.assertEqual(self.client.get("/admin/reporte-cliente-pdf/9999").status_code, 404)  # lote A
        self.assertEqual(self.client.get("/admin/reportes/cliente/9999/pdf").status_code, 404)

    def test_requiere_admin(self):
        self.assertRedirects(Client().get("/admin/reportes"), "/admin/login", fetch_redirect_response=False)
