from django.test import Client, TestCase

from core.models import Cliente, Vehiculo
from core.tests.fabricas import crear_usuario, login_admin
from reportes.tests.test_filtros import datos_reportes


class VistasReportesTests(TestCase):
    def setUp(self):
        login_admin(self.client, crear_usuario())
        self.joel, self.ana, self.sensores = datos_reportes()

    def test_reportes(self):
        r = self.client.get("/admin/reportes")
        self.assertEqual((r.context["tiposSensor"], r.context["marcas"], r.context["tiposPlaca"]),
                         (["ECT", "MAF", "O2", "TEST"], ["Chevrolet", "Kia"],
                          ["particular", "publico", "oficial", "diplomatico"]))
        self.assertEqual((r.context["totalFallas"], r.context["totalAdvertencias"]), (1, 1))
        self.assertEqual([v.placa for v in r.context["vehiculosConFallas"]], ["KIA111"])

    def test_totales_respetan_filtros(self):  # lote A
        r = self.client.get("/admin/reportes-filtrado?tipoPlaca=publico")
        self.assertEqual((r.context["totalVehiculos"], r.context["vehiculosConFallas"], r.context["clientesBloqueados"]),
                         (1, [], []))
        r = self.client.get("/admin/reportes-filtrado?estadoSensor=optimo")
        self.assertEqual(r.context["vehiculosConFallas"], [])
        r = self.client.get("/admin/reportes-filtrado")
        self.assertEqual([v.placa for v in r.context["vehiculosConFallas"]], ["KIA111"])
        self.assertEqual([c.correo for c in r.context["clientesBloqueados"]], ["ana@test.com"])

    def test_enlaces_a_vistas_imprimibles(self):  # lote A
        r = self.client.get("/admin/reportes")
        self.assertContains(r, 'href="/admin/reportes-pdf"')
        self.assertContains(r, f'href="/admin/reporte-cliente-pdf/{self.joel.pk}"')

    def test_reporte_cliente_estado_vacio(self):  # lote A
        Cliente.objects.filter(pk=self.joel.pk).update(estado=None)
        self.assertNotContains(self.client.get(f"/admin/reporte-cliente-pdf/{self.joel.pk}"), "NONE")

    def test_placa_vacia_no_muestra_null(self):  # lote A
        Vehiculo.objects.filter(placa="KIA111").update(placa=None)
        for url in ("/admin/reportes", "/admin/reportes-pdf"):
            self.assertNotContains(self.client.get(url), ">null<", msg_prefix=url)

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
