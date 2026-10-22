"""Vistas de la web del cliente (equivalen a AuthController, DashboardController y VehiculoController)."""
import re

from django.shortcuts import redirect, render

from core.auth import (cerrar_sesion_cliente, cifrar_contrasena, cliente_requerido, iniciar_sesion_cliente,
                       verificar_contrasena)
from core.http import metodos, parametro
from core.models import Cliente, Sensor, Vehiculo
from core.sensores_defecto import crear_sensores_por_defecto
from core.utilidades import entero_java

FORMATO_PLACA = r"[A-Z]{3}-?[0-9]{3}"


@metodos("GET")
def inicio(request):
    """Equivale a AuthController.home."""
    return render(request, "paginas/index.html")


@metodos("GET")
def nosotros(request):
    """Equivale a AuthController.nosotros."""
    return render(request, "paginas/nosotros.html")


@metodos("GET", "POST")
def login(request):
    """Equivale a AuthController.showLogin + formLogin de Spring (ClienteUserDetailsService)."""
    if request.method != "POST":
        return render(request, "paginas/login.html")
    correo = request.POST.get("correo", "")
    contrasena = request.POST.get("contrasena", "")
    cliente = Cliente.objects.filter(correo__iexact=correo).first()
    if cliente is None or cliente.estado == "bloqueado" or not verificar_contrasena(contrasena, cliente.contrasena):
        return redirect("/login?error")
    iniciar_sesion_cliente(request, cliente)
    return redirect("/dashboard")


def logout(request):
    """Equivale al logout de Spring en /logout (cualquier método, como con CSRF desactivado)."""
    cerrar_sesion_cliente(request)
    return redirect("/login")


@metodos("GET", "POST")
def register(request):
    """Equivale a AuthController.showRegister / register (sin recortar espacios, como en Java)."""
    if request.method != "POST":
        return render(request, "paginas/register.html")
    nombre = parametro(request, "nombre")
    apellido = parametro(request, "apellido")
    correo = parametro(request, "correo")
    contrasena = parametro(request, "contrasena")
    if Cliente.objects.filter(correo__iexact=correo).exists():
        return render(request, "paginas/register.html", {"error": "El correo ya está registrado."})
    Cliente.objects.create(
        nombre_cliente=nombre,
        apellido_cliente=apellido,
        correo=correo,
        contrasena=cifrar_contrasena(contrasena),
        estado="activo",
    )
    return redirect("/login")


# ---------------------------------------------------------------------------
# DashboardController
# ---------------------------------------------------------------------------
@cliente_requerido
@metodos("GET")
def dashboard(request):
    """Equivale a DashboardController.dashboard."""
    cliente = request.cliente
    vehiculos = list(Vehiculo.objects.filter(cliente=cliente))
    ids = [v.id_vehiculo for v in vehiculos]
    sensores = list(Sensor.objects.filter(vehiculo_id__in=ids)) if ids else []
    contexto = {
        "cliente": cliente,
        "vehiculos": vehiculos,
        "totalSensores": len(sensores),
        "sensoresOk": sum(1 for s in sensores if s.nivel < 40),
        "advertencias": sum(1 for s in sensores if 40 <= s.nivel < 70),
        "fallas": sum(1 for s in sensores if s.nivel >= 70),
    }
    return render(request, "paginas/dashboard.html", contexto)


@cliente_requerido
@metodos("GET")
def mis_vehiculos(request):
    """Equivale a DashboardController.misVehiculos."""
    contexto = {"cliente": request.cliente, "vehiculos": list(Vehiculo.objects.filter(cliente=request.cliente))}
    return render(request, "paginas/mis-vehiculos.html", contexto)


@cliente_requerido
@metodos("GET")
def sensores(request):
    """Equivale a DashboardController.sensores."""
    contexto = {"cliente": request.cliente, "vehiculos": list(Vehiculo.objects.filter(cliente=request.cliente))}
    return render(request, "paginas/sensores.html", contexto)


# ---------------------------------------------------------------------------
# VehiculoController
# ---------------------------------------------------------------------------
@cliente_requerido
@metodos("GET", "POST")
def vehiculo_crear(request):
    """Equivale a VehiculoController.showCrear / crear."""
    if request.method != "POST":
        return render(request, "paginas/crear-vehiculo.html")
    nombre_vehiculo = parametro(request, "nombreVehiculo")
    marca = parametro(request, "marca")
    modelo = parametro(request, "modelo")
    color = parametro(request, "color")
    placa = parametro(request, "placa")
    tipo_placa = parametro(request, "tipoPlaca")

    def error(mensaje):
        return render(request, "paginas/crear-vehiculo.html", {"error": mensaje})

    if any(c.strip() == "" for c in (nombre_vehiculo, marca, modelo, color, placa, tipo_placa)):
        return error("Todos los campos son obligatorios.")
    anio = entero_java(modelo)
    if anio is None:
        return error("El año debe ser un número válido.")
    if anio < 1990 or anio > 2030:
        return error("El año debe estar entre 1990 y 2030.")
    if Vehiculo.objects.filter(placa__iexact=placa.upper()).exists():
        return error("Ya existe un vehículo registrado con esa placa.")
    if not re.fullmatch(FORMATO_PLACA, placa.upper()):
        return error("Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")

    vehiculo = Vehiculo.objects.create(
        nombre_vehiculo=nombre_vehiculo.strip(),
        marca=marca.strip(),
        modelo=modelo + "-01-01",
        color=color.strip(),
        placa=placa.upper().strip(),
        tipo_placa=tipo_placa,
        cliente=request.cliente,
    )
    crear_sensores_por_defecto(vehiculo)
    return redirect("/vehiculos")


@cliente_requerido
@metodos("GET", "POST")
def vehiculo_editar(request, id):
    """Equivale a VehiculoController.showEditar / editar."""
    if request.method == "POST":
        nombre_vehiculo = parametro(request, "nombreVehiculo")
        marca = parametro(request, "marca")
        color = parametro(request, "color")
        placa = parametro(request, "placa")
        tipo_placa = parametro(request, "tipoPlaca")
    cliente = request.cliente
    vehiculo = Vehiculo.objects.get(pk=id)
    if vehiculo.cliente_id != cliente.id_cliente:
        return redirect("/vehiculos")
    if request.method != "POST":
        return render(request, "paginas/editar-vehiculo.html", {"vehiculo": vehiculo, "cliente": cliente})

    def error(mensaje):
        return render(request, "paginas/editar-vehiculo.html",
                      {"error": mensaje, "vehiculo": vehiculo, "cliente": cliente})

    if any(c.strip() == "" for c in (nombre_vehiculo, marca, color, placa)):
        return error("Todos los campos son obligatorios.")
    if placa.upper() != vehiculo.placa and Vehiculo.objects.filter(placa__iexact=placa.upper()).exists():
        return error("Ya existe un vehículo con esa placa.")

    vehiculo.nombre_vehiculo = nombre_vehiculo.strip()
    vehiculo.marca = marca.strip()
    vehiculo.color = color.strip()
    vehiculo.placa = placa.upper().strip()
    vehiculo.tipo_placa = tipo_placa
    vehiculo.save()
    return redirect("/vehiculos")


@cliente_requerido
@metodos("POST")
def vehiculo_eliminar(request, id):
    """Equivale a VehiculoController.eliminar. Los sensores se borran en cascada y las lecturas se conservan (F3)."""
    vehiculo = Vehiculo.objects.get(pk=id)
    if vehiculo.cliente_id == request.cliente.id_cliente:
        vehiculo.delete()
    return redirect("/vehiculos")
