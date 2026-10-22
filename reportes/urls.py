from django.urls import path

from reportes import views

urlpatterns = [
    path("admin/reportes", views.reportes, name="admin_reportes"),
    path("admin/reportes-filtrado", views.reportes_filtrado, name="admin_reportes_filtrado"),
    path("admin/reportes-pdf", views.reporte_general, name="admin_reportes_pdf_vista"),
    path("admin/reporte-cliente-pdf/<int:cliente_id>", views.reporte_cliente, name="admin_reporte_cliente_vista"),
    path("admin/reportes/csv/<str:tipo>", views.exportar_csv, name="admin_reportes_csv"),
    path("admin/reportes/excel", views.exportar_excel, name="admin_reportes_excel"),
    path("admin/reportes/pdf", views.exportar_pdf, name="admin_reportes_pdf"),
    path("admin/reportes/cliente/<int:id>/pdf", views.exportar_pdf_cliente, name="admin_reportes_cliente_pdf"),
]
