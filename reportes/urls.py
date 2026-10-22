from django.urls import path

from reportes import views

urlpatterns = [
    path("admin/reportes", views.reportes, name="admin_reportes"),
    path("admin/reportes-filtrado", views.reportes_filtrado, name="admin_reportes_filtrado"),
    path("admin/reportes-pdf", views.reporte_general, name="admin_reportes_pdf_vista"),
    path("admin/reporte-cliente-pdf/<int:cliente_id>", views.reporte_cliente, name="admin_reporte_cliente_vista"),
]
