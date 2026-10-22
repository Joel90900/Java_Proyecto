"""Vistas del panel de administración (equivalen a AdminController)."""
from django.shortcuts import redirect, render

from core.auth import (admin_requerido, cerrar_sesion_admin, cifrar_contrasena, iniciar_sesion_admin,
                       verificar_contrasena)
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
    usuario = Usuario.objects.filter(correo__iexact=correo).first()
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
    if Cliente.objects.filter(correo__iexact=correo.strip()).exists():
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
    existente = Cliente.objects.filter(correo__iexact=correo.strip()).first()
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
    if Usuario.objects.filter(correo__iexact=correo.strip()).exists():
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
    existente = Usuario.objects.filter(correo__iexact=correo.strip()).first()
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
