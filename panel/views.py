"""Vistas del panel de administración (equivalen a AdminController)."""
from django.shortcuts import get_object_or_404, redirect, render

from core.auth import (admin_requerido, cerrar_sesion_admin, cifrar_contrasena, iniciar_sesion_admin,
                       verificar_contrasena)
from core.consultas import igual_mysql, placa_duplicada
from core.http import metodos, parametro
from core.models import Cliente, Sensor, Usuario, Vehiculo
from core.normalizacion import normalizar_modelo, normalizar_placa, normalizar_tipo_placa
from core.patrones.singleton import UmbralesReporte
from core.validaciones import validar_largos, validar_persona, validar_vehiculo

PLACA_DUPLICADA = "Ya existe un vehículo registrado con esa placa."


# ---------------------------------------------------------------------------
# Login (formLogin de la cadena de seguridad de /admin/**)
# ---------------------------------------------------------------------------
@metodos("GET", "POST")
def login(request):
    """Equivale a AdminController.loginPage + formLogin de Spring (AdminUserDetailsService)."""
    if request.method != "POST":
        return render(request, "admin/login.html")
    correo = request.POST.get("correo", "").strip()
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
def contrasena_nueva(contrasena: str | None) -> str | None:
    """Al editar, una contraseña vacía o solo con espacios conserva la actual."""
    return None if contrasena is None or contrasena.strip() == "" else contrasena


@admin_requerido
@metodos("POST")
def cliente_estado(request, id):
    """Equivale a AdminController.cambiarEstado."""
    cliente = get_object_or_404(Cliente, pk=id)
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
    """Equivale a AdminController.crearCliente, con las validaciones comunes (lote A)."""
    nombre = parametro(request, "nombre").strip()
    apellido = parametro(request, "apellido").strip()
    correo = parametro(request, "correo").strip()
    contrasena = parametro(request, "contrasena")
    error = validar_persona([nombre, apellido], correo, contrasena) or validar_largos(
        Cliente, {"nombre_cliente": nombre, "apellido_cliente": apellido, "correo": correo})
    if error is None and igual_mysql(Cliente.objects.all(), "correo", correo).exists():
        error = "Ya existe un cliente con ese correo."
    if error:
        return render(request, "admin/crear-cliente.html", {"error": error})
    Cliente.objects.create(
        nombre_cliente=nombre,
        apellido_cliente=apellido,
        correo=correo,
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
    """Equivale a AdminController.showEditarCliente / editarCliente, con las validaciones comunes (lote A)."""
    if request.method != "POST":
        cliente = get_object_or_404(Cliente, pk=id)
        return render(request, "admin/editar-cliente.html", {"cliente": cliente, "error": ""})
    nombre = parametro(request, "nombre").strip()
    apellido = parametro(request, "apellido").strip()
    correo = parametro(request, "correo").strip()
    contrasena = contrasena_nueva(parametro(request, "contrasena", requerido=False))
    cliente = get_object_or_404(Cliente, pk=id)
    error = validar_persona([nombre, apellido], correo, contrasena, contrasena_obligatoria=False) or validar_largos(
        Cliente, {"nombre_cliente": nombre, "apellido_cliente": apellido, "correo": correo})
    if error is None and igual_mysql(Cliente.objects.exclude(pk=cliente.pk), "correo", correo).exists():
        error = "Ya existe un cliente con ese correo."
    if error:
        return render(request, "admin/editar-cliente.html", {"cliente": cliente, "error": error})

    cliente.nombre_cliente = nombre
    cliente.apellido_cliente = apellido
    cliente.correo = correo
    if contrasena is not None:
        cliente.contrasena = cifrar_contrasena(contrasena)
    cliente.save()
    return redirect("/admin")


# ---------------------------------------------------------------------------
# Vehículos
# ---------------------------------------------------------------------------
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
    """Equivale a AdminController.crearVehiculo, con las validaciones comunes (lote A).
    Desde el panel no se crean sensores por defecto."""
    cliente_id = parametro(request, "clienteId", int)
    nombre_vehiculo = parametro(request, "nombreVehiculo").strip()
    marca = parametro(request, "marca").strip()
    modelo = (parametro(request, "modelo", requerido=False) or "").strip()
    color = parametro(request, "color").strip()
    placa = normalizar_placa(parametro(request, "placa"))
    tipo_placa = parametro(request, "tipoPlaca")
    elm_mac = parametro(request, "elmMac", requerido=False)

    error = validar_vehiculo(nombre_vehiculo, marca, modelo, color, placa, tipo_placa) or validar_largos(
        Vehiculo, {"nombre_vehiculo": nombre_vehiculo, "marca": marca, "color": color, "elm_mac": opcional(elm_mac)})
    if error is None and placa_duplicada(placa):
        error = PLACA_DUPLICADA
    cliente = Cliente.objects.filter(pk=cliente_id).first()
    if error is None and cliente is None:
        error = "Selecciona un cliente válido."
    if error:
        return render(request, "admin/crear-vehiculo.html", {"clientes": list(Cliente.objects.all()), "error": error})
    Vehiculo.objects.create(
        cliente=cliente,
        nombre_vehiculo=nombre_vehiculo,
        marca=marca,
        modelo=normalizar_modelo(modelo),
        color=color,
        placa=placa,
        tipo_placa=normalizar_tipo_placa(tipo_placa),
        elm_mac=opcional(elm_mac),
    )
    return redirect("/admin")


@admin_requerido
@metodos("GET", "POST")
def vehiculo_editar(request, id):
    """Equivale a AdminController.showEditarVehiculo / editarVehiculo, con las validaciones comunes (lote A).
    Un modelo vacío conserva el actual."""
    if request.method != "POST":
        vehiculo = get_object_or_404(Vehiculo, pk=id)
        return render(request, "admin/editar-vehiculo.html",
                      {"vehiculo": vehiculo, "clientes": list(Cliente.objects.all()), "error": ""})
    cliente_id = parametro(request, "clienteId", int, requerido=False)
    nombre_vehiculo = parametro(request, "nombreVehiculo").strip()
    marca = parametro(request, "marca").strip()
    modelo = opcional(parametro(request, "modelo", requerido=False))
    color = parametro(request, "color").strip()
    placa = normalizar_placa(parametro(request, "placa"))
    tipo_placa = parametro(request, "tipoPlaca")
    elm_mac = parametro(request, "elmMac", requerido=False)
    vehiculo = get_object_or_404(Vehiculo, pk=id)

    error = validar_vehiculo(nombre_vehiculo, marca, modelo, color, placa, tipo_placa,
                             modelo_obligatorio=False) or validar_largos(
        Vehiculo, {"nombre_vehiculo": nombre_vehiculo, "marca": marca, "color": color, "elm_mac": opcional(elm_mac)})
    if error is None and placa_duplicada(placa, vehiculo):
        error = PLACA_DUPLICADA
    if error:
        return render(request, "admin/editar-vehiculo.html",
                      {"vehiculo": vehiculo, "clientes": list(Cliente.objects.all()), "error": error})

    vehiculo.nombre_vehiculo = nombre_vehiculo
    vehiculo.marca = marca
    if modelo is not None:
        vehiculo.modelo = normalizar_modelo(modelo)
    vehiculo.color = color
    vehiculo.placa = placa
    vehiculo.tipo_placa = normalizar_tipo_placa(tipo_placa)
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


def _validar_sensor(nombre_sensor, tipo_sensor, nivel, vehiculo_id, tipo_dano):
    """Validaciones comunes de crearSensor/editarSensor: devuelve (mensaje de error, vehículo)."""
    if nombre_sensor.strip() == "" or tipo_sensor.strip() == "" or nivel is None:
        return "Todos los campos obligatorios deben estar completos.", None
    if nivel < 0 or nivel > 100:
        return "El nivel debe estar entre 0 y 100.", None
    largo = validar_largos(Sensor, {"nombre_sensor": nombre_sensor.strip(), "tipo_sensor": tipo_sensor.strip(),
                                    "tipo_dano": opcional(tipo_dano)})
    if largo:
        return largo, None
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
    mensaje, vehiculo = _validar_sensor(nombre_sensor, tipo_sensor, nivel, vehiculo_id, tipo_dano)
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
        sensor = get_object_or_404(Sensor, pk=id)
        return render(request, "admin/editar-sensor.html",
                      {"vehiculos": list(Vehiculo.objects.all()), "sensor": sensor, "error": ""})
    vehiculo_id = parametro(request, "vehiculoId", int)
    nombre_sensor = parametro(request, "nombreSensor")
    tipo_sensor = parametro(request, "tipoSensor")
    nivel = parametro(request, "nivel", int)
    tipo_dano = parametro(request, "tipoDano", requerido=False)
    sensor = get_object_or_404(Sensor, pk=id)
    mensaje, vehiculo = _validar_sensor(nombre_sensor, tipo_sensor, nivel, vehiculo_id, tipo_dano)
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
    """Equivale a AdminController.crearUsuario (el rol es texto libre, S2), con las validaciones comunes (lote A)."""
    nombre = parametro(request, "nombre").strip()
    correo = parametro(request, "correo").strip()
    contrasena = parametro(request, "contrasena")
    rol = parametro(request, "rol")
    error = validar_persona([nombre], correo, contrasena) or validar_largos(
        Usuario, {"nombre": nombre, "correo": correo, "rol": rol.strip()})
    if error is None and igual_mysql(Usuario.objects.all(), "correo", correo).exists():
        error = "Ya existe un usuario con ese correo."
    if error:
        return render(request, "admin/crear-usuario.html", {"error": error})
    Usuario.objects.create(
        nombre=nombre,
        correo=correo,
        contrasena=cifrar_contrasena(contrasena),
        rol="ADMIN" if rol.strip() == "" else rol.strip(),
    )
    return redirect("/admin")


@admin_requerido
@metodos("GET", "POST")
def usuario_editar(request, id):
    """Equivale a AdminController.showEditarUsuario / editarUsuario, con las validaciones comunes (lote A)."""
    if request.method != "POST":
        usuario = get_object_or_404(Usuario, pk=id)
        return render(request, "admin/editar-usuario.html", {"usuario": usuario, "error": ""})
    nombre = parametro(request, "nombre").strip()
    correo = parametro(request, "correo").strip()
    contrasena = contrasena_nueva(parametro(request, "contrasena", requerido=False))
    rol = parametro(request, "rol")
    usuario = get_object_or_404(Usuario, pk=id)
    error = validar_persona([nombre], correo, contrasena, contrasena_obligatoria=False) or validar_largos(
        Usuario, {"nombre": nombre, "correo": correo, "rol": rol.strip()})
    if error is None and igual_mysql(Usuario.objects.exclude(pk=usuario.pk), "correo", correo).exists():
        error = "Ya existe un usuario con ese correo."
    if error:
        return render(request, "admin/editar-usuario.html", {"usuario": usuario, "error": error})

    usuario.nombre = nombre
    usuario.correo = correo
    if contrasena is not None:
        usuario.contrasena = cifrar_contrasena(contrasena)
    usuario.rol = usuario.rol if rol.strip() == "" else rol.strip()
    usuario.save()
    return redirect("/admin")


@admin_requerido
@metodos("POST")
def usuario_eliminar(request, id):
    """Equivale a AdminController.eliminarUsuario: no se borra a sí mismo ni al último administrador."""
    total_usuarios = Usuario.objects.count()
    usuario = get_object_or_404(Usuario, pk=id)
    if request.admin_correo.lower() == usuario.correo.lower() or total_usuarios <= 1:
        return redirect("/admin")
    usuario.delete()
    return redirect("/admin")
