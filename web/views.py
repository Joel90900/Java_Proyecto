"""Vistas de la web del cliente (equivalen a AuthController, DashboardController y VehiculoController)."""
from django.shortcuts import redirect, render

from core.auth import (cerrar_sesion_cliente, cifrar_contrasena, cliente_requerido, iniciar_sesion_cliente,
                       verificar_contrasena)
from core.consultas import igual_mysql
from core.http import metodos, parametro
from core.models import Cliente, Sensor, Vehiculo
from core.normalizacion import normalizar_modelo, normalizar_placa, normalizar_tipo_placa
from core.sensores_defecto import crear_sensores_por_defecto
from core.validaciones import validar_persona, validar_vehiculo

PLACA_DUPLICADA = "Ya existe un vehículo registrado con esa placa."


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
    correo = request.POST.get("correo", "").strip()
    contrasena = request.POST.get("contrasena", "")
    cliente = igual_mysql(Cliente.objects.all(), "correo", correo).first()
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
    """Equivale a AuthController.showRegister / register, con las validaciones comunes (lote A)."""
    if request.method != "POST":
        return render(request, "paginas/register.html")
    nombre = parametro(request, "nombre").strip()
    apellido = parametro(request, "apellido").strip()
    correo = parametro(request, "correo").strip()
    contrasena = parametro(request, "contrasena")
    error = validar_persona([nombre, apellido], correo, contrasena)
    if error is None and igual_mysql(Cliente.objects.all(), "correo", correo).exists():
        error = "El correo ya está registrado."
    if error:
        return render(request, "paginas/register.html", {"error": error})
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
    """Equivale a VehiculoController.showCrear / crear, con las validaciones comunes (lote A)."""
    if request.method != "POST":
        return render(request, "paginas/crear-vehiculo.html")
    nombre_vehiculo = parametro(request, "nombreVehiculo").strip()
    marca = parametro(request, "marca").strip()
    modelo = parametro(request, "modelo").strip()
    color = parametro(request, "color").strip()
    placa = normalizar_placa(parametro(request, "placa"))
    tipo_placa = parametro(request, "tipoPlaca")

    error = validar_vehiculo(nombre_vehiculo, marca, modelo, color, placa, tipo_placa)
    if error is None and igual_mysql(Vehiculo.objects.all(), "placa", placa).exists():
        error = PLACA_DUPLICADA
    if error:
        return render(request, "paginas/crear-vehiculo.html", {"error": error})

    vehiculo = Vehiculo.objects.create(
        nombre_vehiculo=nombre_vehiculo,
        marca=marca,
        modelo=normalizar_modelo(modelo),
        color=color,
        placa=placa,
        tipo_placa=normalizar_tipo_placa(tipo_placa),
        cliente=request.cliente,
    )
    crear_sensores_por_defecto(vehiculo)
    return redirect("/vehiculos")


@cliente_requerido
@metodos("GET", "POST")
def vehiculo_editar(request, id):
    """Equivale a VehiculoController.showEditar / editar, con las validaciones comunes (lote A)."""
    if request.method == "POST":
        nombre_vehiculo = parametro(request, "nombreVehiculo").strip()
        marca = parametro(request, "marca").strip()
        color = parametro(request, "color").strip()
        placa = normalizar_placa(parametro(request, "placa"))
        tipo_placa = parametro(request, "tipoPlaca")
    cliente = request.cliente
    vehiculo = Vehiculo.objects.get(pk=id)
    if vehiculo.cliente_id != cliente.id_cliente:
        return redirect("/vehiculos")
    if request.method != "POST":
        return render(request, "paginas/editar-vehiculo.html", {"vehiculo": vehiculo, "cliente": cliente})

    error = validar_vehiculo(nombre_vehiculo, marca, None, color, placa, tipo_placa, modelo_obligatorio=False)
    otros = Vehiculo.objects.exclude(pk=vehiculo.pk)
    if error is None and igual_mysql(otros, "placa", placa).exists():
        error = PLACA_DUPLICADA
    if error:
        return render(request, "paginas/editar-vehiculo.html", {"error": error, "vehiculo": vehiculo, "cliente": cliente})

    vehiculo.nombre_vehiculo = nombre_vehiculo
    vehiculo.marca = marca
    vehiculo.color = color
    vehiculo.placa = placa
    vehiculo.tipo_placa = normalizar_tipo_placa(tipo_placa)
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
