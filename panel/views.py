"""Vistas del panel de administración (equivalen a AdminController)."""
import re

from django.shortcuts import redirect, render

from core.auth import (admin_requerido, cerrar_sesion_admin, cifrar_contrasena, iniciar_sesion_admin,
                       verificar_contrasena)
from core.consultas import igual_mysql
from core.http import metodos, parametro
from core.models import Cliente, Sensor, Usuario, Vehiculo
from core.patrones.singleton import UmbralesReporte


# ---------------------------------------------------------------------------
# Login (formLogin de la cadena de seguridad de /admin/**)
# ---------------------------------------------------------------------------
@metodos("GET", "POST")
def login(request):
    """Equivale a AdminController.loginPage + formLogin de Spring (AdminUserDetailsService)."""
    if request.method != "POST":
        return render(request, "admin/login.html")
    correo = request.POST.get("correo", "")
    contrasena = request.POST.get("contrasena", "")
    usuario = igual_mysql(Usuario.objects.all(), "correo", correo).first()
    if usuario is None or not verificar_contrasena(contrasena, usuario.contrasena):
        return redirect("/admin/login?error")
    iniciar_sesion_admin(request, usuario)
    return redirect("/admin")


def logout(request):
    """Equivale al logout de Spring en /admin/logout."""
    cerrar_sesion_admin(request)
    return redirect("/admin/login")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def cargar_totales(contexto: dict) -> None:
    """Equivale a AdminController.cargarTotales."""
    sensores = list(Sensor.objects.all())
    umbrales = UmbralesReporte.INSTANCIA
    total_fallas = sum(1 for s in sensores if s.nivel is not None and umbrales.es_falla(s.nivel))
    total_advertencias = sum(1 for s in sensores if s.nivel is not None and umbrales.es_advertencia(s.nivel))
    contexto.update({
        "totalClientes": Cliente.objects.count(),
        "totalVehiculos": Vehiculo.objects.count(),
        "totalSensores": len(sensores),
        "totalUsuarios": Usuario.objects.count(),
        "totalFallas": total_fallas,
        "totalAdvertencias": total_advertencias,
        "sensoresOk": len(sensores) - total_fallas - total_advertencias,
    })


@admin_requerido
@metodos("GET")
def index(request):
    """Equivale a AdminController.index."""
    contexto = {
        "clientes": list(Cliente.objects.all()),
        "vehiculos": list(Vehiculo.objects.all()),
        "sensores": list(Sensor.objects.all()),
        "usuarios": list(Usuario.objects.all()),
    }
    cargar_totales(contexto)
    return render(request, "admin/dashboard.html", contexto)


@admin_requerido
@metodos("GET")
def nosotros(request):
    """Equivale a AdminController.nosotrosPage."""
    return render(request, "paginas/nosotros.html")


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------
def correo_valido(correo: str) -> bool:
    return "@" in correo and "." in correo


@admin_requerido
@metodos("POST")
def cliente_estado(request, id):
    """Equivale a AdminController.cambiarEstado."""
    cliente = Cliente.objects.get(pk=id)
    cliente.estado = "bloqueado" if cliente.estado == "activo" else "activo"
    cliente.save()
    return redirect("/admin")


@admin_requerido
@metodos("GET")
def cliente_nuevo(request):
    """Equivale a AdminController.nuevoCliente."""
    return render(request, "admin/crear-cliente.html", {"error": ""})


@admin_requerido
@metodos("POST")
def cliente_crear(request):
    """Equivale a AdminController.crearCliente."""
    nombre = parametro(request, "nombre")
    apellido = parametro(request, "apellido")
    correo = parametro(request, "correo")
    contrasena = parametro(request, "contrasena")

    def error(mensaje):
        return render(request, "admin/crear-cliente.html", {"error": mensaje})

    if any(c.strip() == "" for c in (nombre, apellido, correo, contrasena)):
        return error("Todos los campos son obligatorios.")
    if not correo_valido(correo):
        return error("El correo no tiene un formato válido.")
    if len(contrasena) < 6:
        return error("La contraseña debe tener al menos 6 caracteres.")
    if igual_mysql(Cliente.objects.all(), "correo", correo.strip()).exists():
        return error("Ya existe un cliente con ese correo.")
    Cliente.objects.create(
        nombre_cliente=nombre.strip(),
        apellido_cliente=apellido.strip(),
        correo=correo.strip(),
        contrasena=cifrar_contrasena(contrasena),
        estado="activo",
    )
    return redirect("/admin")


@admin_requerido
@metodos("POST")
def cliente_eliminar(request, id):
    """Equivale a AdminController.eliminarCliente: borra sus vehículos (y sensores) y luego al cliente (F3)."""
    for vehiculo in Vehiculo.objects.filter(cliente_id=id):
        vehiculo.delete()
    Cliente.objects.filter(pk=id).delete()
    return redirect("/admin")


@admin_requerido
@metodos("GET", "POST")
def cliente_editar(request, id):
    """Equivale a AdminController.showEditarCliente / editarCliente."""
    if request.method != "POST":
        cliente = Cliente.objects.get(pk=id)
        return render(request, "admin/editar-cliente.html", {"cliente": cliente, "error": ""})
    nombre = parametro(request, "nombre")
    apellido = parametro(request, "apellido")
    correo = parametro(request, "correo")
    contrasena = parametro(request, "contrasena", requerido=False)
    cliente = Cliente.objects.get(pk=id)

    def error(mensaje):
        return render(request, "admin/editar-cliente.html", {"cliente": cliente, "error": mensaje})

    if any(c.strip() == "" for c in (nombre, apellido, correo)):
        return error("Todos los campos obligatorios deben estar completos.")
    if not correo_valido(correo):
        return error("El correo no tiene un formato válido.")
    existente = igual_mysql(Cliente.objects.all(), "correo", correo.strip()).first()
    if existente is not None and existente.id_cliente != id:
        return error("Ya existe un cliente con ese correo.")
    nueva_contrasena = contrasena is not None and contrasena.strip() != ""
    if nueva_contrasena and len(contrasena) < 6:
        return error("La contraseña debe tener al menos 6 caracteres.")

    cliente.nombre_cliente = nombre.strip()
    cliente.apellido_cliente = apellido.strip()
    cliente.correo = correo.strip()
    if nueva_contrasena:
        cliente.contrasena = cifrar_contrasena(contrasena)
    cliente.save()
    return redirect("/admin")


# ---------------------------------------------------------------------------
# Vehículos
# ---------------------------------------------------------------------------
FORMATO_PLACA = r"[A-Z]{3}-?[0-9]{3}"


def opcional(texto: str | None) -> str | None:
    """"campo == null || campo.isBlank() ? null : campo.trim()" de Java."""
    return None if texto is None or texto.strip() == "" else texto.strip()


@admin_requerido
@metodos("POST")
def vehiculo_eliminar(request, id):
    """Equivale a AdminController.eliminarVehiculo: sensores en cascada, lecturas conservadas (F3)."""
    Vehiculo.objects.filter(pk=id).delete()
    return redirect("/admin")


@admin_requerido
@metodos("GET")
def vehiculo_nuevo(request):
    """Equivale a AdminController.nuevoVehiculo."""
    return render(request, "admin/crear-vehiculo.html", {"clientes": list(Cliente.objects.all()), "error": ""})


@admin_requerido
@metodos("POST")
def vehiculo_crear(request):
    """Equivale a AdminController.crearVehiculo (desde el panel no se crean sensores por defecto)."""
    cliente_id = parametro(request, "clienteId", int)
    nombre_vehiculo = parametro(request, "nombreVehiculo")
    marca = parametro(request, "marca")
    modelo = parametro(request, "modelo", requerido=False)
    color = parametro(request, "color")
    placa = parametro(request, "placa")
    tipo_placa = parametro(request, "tipoPlaca")
    elm_mac = parametro(request, "elmMac", requerido=False)

    def error(mensaje):
        return render(request, "admin/crear-vehiculo.html", {"clientes": list(Cliente.objects.all()), "error": mensaje})

    placa_normalizada = placa.upper().strip()
    if any(c.strip() == "" for c in (nombre_vehiculo, marca, color, placa_normalizada)):
        return error("Todos los campos obligatorios deben estar completos.")
    if not re.fullmatch(FORMATO_PLACA, placa_normalizada):
        return error("Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")
    if igual_mysql(Vehiculo.objects.all(), "placa", placa_normalizada).exists():
        return error("Ya existe un vehículo con esa placa.")
    cliente = Cliente.objects.filter(pk=cliente_id).first()
    if cliente is None:
        return error("Selecciona un cliente válido.")
    Vehiculo.objects.create(
        cliente=cliente,
        nombre_vehiculo=nombre_vehiculo.strip(),
        marca=marca.strip(),
        modelo=opcional(modelo),
        color=color.strip(),
        placa=placa_normalizada,
        tipo_placa=tipo_placa,
        elm_mac=opcional(elm_mac),
    )
    return redirect("/admin")


@admin_requerido
@metodos("GET", "POST")
def vehiculo_editar(request, id):
    """Equivale a AdminController.showEditarVehiculo / editarVehiculo."""
    if request.method != "POST":
        vehiculo = Vehiculo.objects.get(pk=id)
        return render(request, "admin/editar-vehiculo.html",
                      {"vehiculo": vehiculo, "clientes": list(Cliente.objects.all()), "error": ""})
    cliente_id = parametro(request, "clienteId", int, requerido=False)
    nombre_vehiculo = parametro(request, "nombreVehiculo")
    marca = parametro(request, "marca")
    modelo = parametro(request, "modelo", requerido=False)
    color = parametro(request, "color")
    placa = parametro(request, "placa")
    tipo_placa = parametro(request, "tipoPlaca")
    elm_mac = parametro(request, "elmMac", requerido=False)
    vehiculo = Vehiculo.objects.get(pk=id)

    def error(mensaje):
        return render(request, "admin/editar-vehiculo.html",
                      {"vehiculo": vehiculo, "clientes": list(Cliente.objects.all()), "error": mensaje})

    placa_normalizada = placa.upper().strip()
    if any(c.strip() == "" for c in (nombre_vehiculo, marca, color, placa_normalizada)):
        return error("Todos los campos obligatorios deben estar completos.")
    if not re.fullmatch(FORMATO_PLACA, placa_normalizada):
        return error("Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")
    existente = igual_mysql(Vehiculo.objects.all(), "placa", placa_normalizada).first()
    if existente is not None and existente.id_vehiculo != id:
        return error("Ya existe un vehículo con esa placa.")

    vehiculo.nombre_vehiculo = nombre_vehiculo.strip()
    vehiculo.marca = marca.strip()
    vehiculo.modelo = vehiculo.modelo if opcional(modelo) is None else modelo.strip()
    vehiculo.color = color.strip()
    vehiculo.placa = placa_normalizada
    vehiculo.tipo_placa = tipo_placa
    vehiculo.elm_mac = opcional(elm_mac)
    if cliente_id is not None and vehiculo.cliente_id != cliente_id:
        nuevo_cliente = Cliente.objects.filter(pk=cliente_id).first()
        if nuevo_cliente is not None:
            vehiculo.cliente = nuevo_cliente
    vehiculo.save()
    return redirect("/admin")


# ---------------------------------------------------------------------------
# Sensores
# ---------------------------------------------------------------------------
def estado_desde_nivel(nivel: int) -> str:
    """Equivale a AdminController.estadoDesdeNivel."""
    if nivel >= 70:
        return "FALLA"
    if nivel >= 40:
        return "ADVERTENCIA"
    return "OK"


@admin_requerido
@metodos("POST")
def sensor_eliminar(request, id):
    """Equivale a AdminController.eliminarSensor."""
    Sensor.objects.filter(pk=id).delete()
    return redirect("/admin")


@admin_requerido
@metodos("GET")
def sensor_nuevo(request):
    """Equivale a AdminController.nuevoSensor."""
    return render(request, "admin/crear-sensor.html", {"vehiculos": list(Vehiculo.objects.all()), "error": ""})


def _validar_sensor(nombre_sensor, tipo_sensor, nivel, vehiculo_id):
    """Validaciones comunes de crearSensor/editarSensor: devuelve (mensaje de error, vehículo)."""
    if nombre_sensor.strip() == "" or tipo_sensor.strip() == "" or nivel is None:
        return "Todos los campos obligatorios deben estar completos.", None
    if nivel < 0 or nivel > 100:
        return "El nivel debe estar entre 0 y 100.", None
    vehiculo = Vehiculo.objects.filter(pk=vehiculo_id).first()
    if vehiculo is None:
        return "Selecciona un vehículo válido.", None
    return None, vehiculo


@admin_requerido
@metodos("POST")
def sensor_crear(request):
    """Equivale a AdminController.crearSensor (tipo de daño opcional, F4)."""
    vehiculo_id = parametro(request, "vehiculoId", int)
    nombre_sensor = parametro(request, "nombreSensor")
    tipo_sensor = parametro(request, "tipoSensor")
    nivel = parametro(request, "nivel", int)
    tipo_dano = parametro(request, "tipoDano", requerido=False)
    mensaje, vehiculo = _validar_sensor(nombre_sensor, tipo_sensor, nivel, vehiculo_id)
    if mensaje:
        return render(request, "admin/crear-sensor.html", {"vehiculos": list(Vehiculo.objects.all()), "error": mensaje})
    Sensor.objects.create(
        vehiculo=vehiculo,
        nombre_sensor=nombre_sensor.strip(),
        tipo_sensor=tipo_sensor.strip(),
        nivel=nivel,
        tipo_dano=opcional(tipo_dano),
        estado=estado_desde_nivel(nivel),
    )
    return redirect("/admin")


@admin_requerido
@metodos("GET", "POST")
def sensor_editar(request, id):
    """Equivale a AdminController.showEditarSensor / editarSensor."""
    if request.method != "POST":
        sensor = Sensor.objects.get(pk=id)
        return render(request, "admin/editar-sensor.html",
                      {"vehiculos": list(Vehiculo.objects.all()), "sensor": sensor, "error": ""})
    vehiculo_id = parametro(request, "vehiculoId", int)
    nombre_sensor = parametro(request, "nombreSensor")
    tipo_sensor = parametro(request, "tipoSensor")
    nivel = parametro(request, "nivel", int)
    tipo_dano = parametro(request, "tipoDano", requerido=False)
    sensor = Sensor.objects.get(pk=id)
    mensaje, vehiculo = _validar_sensor(nombre_sensor, tipo_sensor, nivel, vehiculo_id)
    if mensaje:
        return render(request, "admin/editar-sensor.html",
                      {"vehiculos": list(Vehiculo.objects.all()), "sensor": sensor, "error": mensaje})
    sensor.vehiculo = vehiculo
    sensor.nombre_sensor = nombre_sensor.strip()
    sensor.tipo_sensor = tipo_sensor.strip()
    sensor.nivel = nivel
    sensor.tipo_dano = opcional(tipo_dano)
    sensor.estado = estado_desde_nivel(nivel)
    sensor.save()
    return redirect("/admin")


# ---------------------------------------------------------------------------
# Usuarios administradores
# ---------------------------------------------------------------------------
@admin_requerido
@metodos("GET")
def usuario_nuevo(request):
    """Equivale a AdminController.nuevoUsuario."""
    return render(request, "admin/crear-usuario.html", {"error": ""})


@admin_requerido
@metodos("POST")
def usuario_crear(request):
    """Equivale a AdminController.crearUsuario (el rol es texto libre, S2)."""
    nombre = parametro(request, "nombre")
    correo = parametro(request, "correo")
    contrasena = parametro(request, "contrasena")
    rol = parametro(request, "rol")

    def error(mensaje):
        return render(request, "admin/crear-usuario.html", {"error": mensaje})

    if any(c.strip() == "" for c in (nombre, correo, contrasena)):
        return error("Todos los campos son obligatorios.")
    if not correo_valido(correo):
        return error("El correo no tiene un formato válido.")
    if len(contrasena) < 6:
        return error("La contraseña debe tener al menos 6 caracteres.")
    if igual_mysql(Usuario.objects.all(), "correo", correo.strip()).exists():
        return error("Ya existe un usuario con ese correo.")
    Usuario.objects.create(
        nombre=nombre.strip(),
        correo=correo.strip(),
        contrasena=cifrar_contrasena(contrasena),
        rol="ADMIN" if rol.strip() == "" else rol.strip(),
    )
    return redirect("/admin")


@admin_requerido
@metodos("GET", "POST")
def usuario_editar(request, id):
    """Equivale a AdminController.showEditarUsuario / editarUsuario."""
    if request.method != "POST":
        usuario = Usuario.objects.get(pk=id)
        return render(request, "admin/editar-usuario.html", {"usuario": usuario, "error": ""})
    nombre = parametro(request, "nombre")
    correo = parametro(request, "correo")
    contrasena = parametro(request, "contrasena", requerido=False)
    rol = parametro(request, "rol")
    usuario = Usuario.objects.get(pk=id)

    def error(mensaje):
        return render(request, "admin/editar-usuario.html", {"usuario": usuario, "error": mensaje})

    if any(c.strip() == "" for c in (nombre, correo)):
        return error("Todos los campos obligatorios deben estar completos.")
    if not correo_valido(correo):
        return error("El correo no tiene un formato válido.")
    existente = igual_mysql(Usuario.objects.all(), "correo", correo.strip()).first()
    if existente is not None and existente.id_usuario != id:
        return error("Ya existe un usuario con ese correo.")
    nueva_contrasena = contrasena is not None and contrasena.strip() != ""
    if nueva_contrasena and len(contrasena) < 6:
        return error("La contraseña debe tener al menos 6 caracteres.")

    usuario.nombre = nombre.strip()
    usuario.correo = correo.strip()
    if nueva_contrasena:
        usuario.contrasena = cifrar_contrasena(contrasena)
    usuario.rol = usuario.rol if rol.strip() == "" else rol.strip()
    usuario.save()
    return redirect("/admin")


@admin_requerido
@metodos("POST")
def usuario_eliminar(request, id):
    """Equivale a AdminController.eliminarUsuario: no se borra a sí mismo ni al último administrador."""
    total_usuarios = Usuario.objects.count()
    usuario = Usuario.objects.get(pk=id)
    if request.admin_correo.lower() == usuario.correo.lower() or total_usuarios <= 1:
        return redirect("/admin")
    usuario.delete()
    return redirect("/admin")
