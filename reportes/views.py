"""Vistas de reportes (equivalen a ReporteController y a AdminController.reportes y exportaciones)."""
import time

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from core.auth import admin_requerido
from core.http import metodos
from core.models import Cliente, Sensor, Vehiculo
from core.patrones.singleton import UmbralesReporte
from core.utilidades import ahora, redondear_java
from reportes.exportar import csv_reporte, datos_pdf_general, excel_reporte, pdf_cliente, pdf_general
from reportes.filtros import (STRATEGY_FILTRO, filtrar_clientes, filtrar_sensores, nz_nivel, ordenar_sensores,
                              parametros_filtro)

TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

TIPOS_PLACA = ["particular", "publico"]


def vehiculos_con_fallas(con_nivel_nulo_como_cero: bool) -> list:
    umbrales = UmbralesReporte.INSTANCIA
    resultado = []
    for v in Vehiculo.objects.all():
        for s in v.sensores.all():
            nivel = nz_nivel(s) if con_nivel_nulo_como_cero else s.nivel
            if nivel is not None and umbrales.es_falla(nivel):
                resultado.append(v)
                break
    return resultado


@admin_requerido
@metodos("GET")
def reportes(request):
    """Equivale a AdminController.reportes + cargarDatosReportes."""
    clientes = list(Cliente.objects.all())
    sensores = list(Sensor.objects.all())
    umbrales = UmbralesReporte.INSTANCIA
    contexto = {
        "clientes": clientes,
        "todosSensores": sensores,
        "clientesBloqueados": [c for c in clientes if c.estado == "bloqueado"],
        "vehiculosConFallas": vehiculos_con_fallas(con_nivel_nulo_como_cero=False),
        "totalClientes": len(clientes),
        "totalVehiculos": Vehiculo.objects.count(),
        "totalSensores": len(sensores),
        "totalFallas": sum(1 for s in sensores if s.nivel is not None and umbrales.es_falla(s.nivel)),
        "totalAdvertencias": sum(1 for s in sensores if s.nivel is not None and umbrales.es_advertencia(s.nivel)),
        # Valores por defecto de los filtros del formulario
        "q": "", "estadoCliente": "", "estadoSensor": "", "tipoSensor": "", "marca": "", "tipoPlaca": "",
        "nivelMin": None, "nivelMax": None, "ordenarPor": "",
        "tiposSensor": sorted({s.tipo_sensor for s in sensores if s.tipo_sensor and s.tipo_sensor.strip()}),
        "marcas": sorted({v.marca for v in Vehiculo.objects.all() if v.marca and v.marca.strip()}),
        "tiposPlaca": TIPOS_PLACA,
    }
    return render(request, "admin/reportes.html", contexto)


@admin_requerido
@metodos("GET")
def reportes_filtrado(request):
    """Equivale a ReporteController.listaReportes (con el filtro de tipo de placa aplicado, F5)."""
    filtros = parametros_filtro(request)
    todos = list(Sensor.objects.all())
    sensores = ordenar_sensores(
        filtrar_sensores(todos, filtros["estadoSensor"], filtros["tipoSensor"], filtros["nivelMin"], filtros["nivelMax"]),
        filtros["ordenarPor"])
    todos_clientes = list(Cliente.objects.all())
    clientes = filtrar_clientes(todos_clientes, filtros["q"], filtros["estadoCliente"], filtros["marca"],
                                filtros["tipoPlaca"])
    umbrales = UmbralesReporte.INSTANCIA
    contexto = {
        "clientes": clientes,
        "todosSensores": sensores,
        "clientesBloqueados": [c for c in todos_clientes if c.estado == "bloqueado"],
        "vehiculosConFallas": vehiculos_con_fallas(con_nivel_nulo_como_cero=True),
        "totalClientes": len(clientes),
        "totalVehiculos": Vehiculo.objects.count(),
        "totalSensores": len(sensores),
        "totalFallas": sum(1 for s in sensores if umbrales.es_falla(nz_nivel(s))),
        "totalAdvertencias": sum(1 for s in sensores if umbrales.es_advertencia(nz_nivel(s))),
        **filtros,
        # Orden de aparición (LinkedHashSet en Java), a diferencia de /admin/reportes que los ordena.
        "tiposSensor": list(dict.fromkeys(s.tipo_sensor for s in todos if s.tipo_sensor is not None)),
        "marcas": list(dict.fromkeys(v.marca for v in Vehiculo.objects.all() if v.marca is not None)),
        "tiposPlaca": TIPOS_PLACA,
    }
    return render(request, "admin/reportes.html", contexto)


@admin_requerido
@metodos("GET")
def reporte_general(request):
    """Equivale a ReporteController.reporteGeneral (informe imprimible)."""
    vehiculos = list(Vehiculo.objects.all())
    sensores = list(Sensor.objects.all())
    conteo = {"optimo": 0, "advertencia": 0, "falla": 0}
    for s in sensores:
        conteo[STRATEGY_FILTRO.clasificar(s.nivel)] += 1
    umbrales = UmbralesReporte.INSTANCIA
    alertas = [s for s in sensores if umbrales.es_advertencia(nz_nivel(s)) or umbrales.es_falla(nz_nivel(s))]
    total = len(sensores)
    contexto = {
        "vehiculos": vehiculos,
        "sensores": sensores,
        "alertas": alertas,
        "totalVehiculos": len(vehiculos),
        "totalSensores": total,
        "saludFlota": 100 if total == 0 else redondear_java(conteo["optimo"] * 100.0 / total),
        "sensoresOptimos": conteo["optimo"],
        "sensoresAdvertencia": conteo["advertencia"],
        "sensoresFalla": conteo["falla"],
        "fechaGeneracion": ahora(),
        "adminNombre": "Administrador",
        "reporteId": f"RPT-{int(time.time() * 1000)}",
    }
    return render(request, "admin/reportes-pdf.html", contexto)


@admin_requerido
@metodos("GET")
def reporte_cliente(request, cliente_id):
    """Equivale a ReporteController.reporteCliente (informe imprimible por cliente)."""
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    contexto = {
        "cliente": cliente,
        "vehiculos": list(Vehiculo.objects.filter(cliente_id=cliente_id)),
        "fechaGeneracion": ahora(),
        "adminNombre": "Administrador",
        "reporteId": f"RPT-{int(time.time() * 1000)}",
    }
    return render(request, "admin/reporte-cliente-pdf.html", contexto)


# ---------------------------------------------------------------------------
# Exportaciones
# ---------------------------------------------------------------------------
def _descarga(contenido, tipo_contenido: str, archivo: str) -> HttpResponse:
    respuesta = HttpResponse(contenido, content_type=tipo_contenido)
    respuesta["Content-Disposition"] = f"attachment; filename={archivo}"
    return respuesta


@admin_requerido
@metodos("GET")
def exportar_csv(request, tipo):
    """Equivale a AdminController.exportarCsv (tipos: clientes, sensores, fallas, bloqueados)."""
    return _descarga(csv_reporte(tipo).encode("utf-8"), "text/csv; charset=UTF-8", f"reporte-{tipo}.csv")


@admin_requerido
@metodos("GET")
def exportar_excel(request):
    """Equivale a ReporteController.exportarExcel, con el filtro de tipo de placa (F5)."""
    filtros = parametros_filtro(request)
    clientes, sensores = datos_pdf_general(filtros)
    return _descarga(excel_reporte(clientes, sensores), TIPO_EXCEL, "reporte-autosen.xlsx")


@admin_requerido
@metodos("GET")
def exportar_pdf(request):
    """Equivale a AdminController.exportarPdfCompleto, aplicando también búsqueda, marca y tipo de placa (F5)."""
    clientes, sensores = datos_pdf_general(parametros_filtro(request))
    return _descarga(pdf_general(clientes, sensores), "application/pdf", "reporte-autosen.pdf")


@admin_requerido
@metodos("GET")
def exportar_pdf_cliente(request, id):
    """Equivale a AdminController.exportarPdfCliente."""
    cliente = get_object_or_404(Cliente, pk=id)
    return _descarga(pdf_cliente(cliente), "application/pdf", f"reporte-{cliente.nombre_cliente.lower()}.pdf")
