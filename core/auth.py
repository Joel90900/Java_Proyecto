"""
Autenticación propia de AutoSen (equivale a SecurityConfig y los UserDetailsService de Java).

Contraseñas: bcrypt compatible con BCryptPasswordEncoder de Spring y con los
hashes $2y$ que generó la versión PHP del proyecto.

Sesiones: cliente y administrador son independientes (F2). En Java ambos
compartían el SecurityContext y un cliente logueado podía entrar a /admin.
"""
from functools import wraps

import bcrypt
from django.shortcuts import redirect

from core.models import Cliente, Usuario

CLAVE_CLIENTE = "cliente_id"
CLAVE_ADMIN = "admin_id"

RUTAS_PUBLICAS = {"/", "/nosotros", "/login", "/register", "/error", "/admin/login"}


def verificar_contrasena(plano: str, hash_guardado: str | None) -> bool:
    """BCryptPasswordEncoder.matches: False ante un hash vacío o inválido."""
    if not hash_guardado:
        return False
    if hash_guardado.startswith("$2y$"):
        hash_guardado = "$2b$" + hash_guardado[4:]
    try:
        return bcrypt.checkpw(plano.encode("utf-8"), hash_guardado.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def cifrar_contrasena(plano: str) -> str:
    """BCryptPasswordEncoder.encode: prefijo $2a$ y costo 10, como Spring."""
    return bcrypt.hashpw(plano.encode("utf-8"), bcrypt.gensalt(rounds=10, prefix=b"2a")).decode("ascii")


def iniciar_sesion_cliente(request, cliente: Cliente) -> None:
    request.session.cycle_key()
    request.session[CLAVE_CLIENTE] = cliente.pk


def cerrar_sesion_cliente(request) -> None:
    request.session.pop(CLAVE_CLIENTE, None)


def cliente_actual(request) -> Cliente | None:
    sesion = getattr(request, "session", None)
    if sesion is None or CLAVE_CLIENTE not in sesion:
        return None
    return Cliente.objects.filter(pk=sesion[CLAVE_CLIENTE]).first()


def iniciar_sesion_admin(request, usuario: Usuario) -> None:
    request.session.cycle_key()
    request.session[CLAVE_ADMIN] = usuario.pk


def cerrar_sesion_admin(request) -> None:
    request.session.pop(CLAVE_ADMIN, None)


def admin_actual(request) -> Usuario | None:
    sesion = getattr(request, "session", None)
    if sesion is None or CLAVE_ADMIN not in sesion:
        return None
    return Usuario.objects.filter(pk=sesion[CLAVE_ADMIN]).first()


def cliente_requerido(vista):
    """Exige sesión de cliente; sin ella redirige a /login (como la cadena de seguridad de clientes)."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        cliente = cliente_actual(request)
        if cliente is None:
            return redirect("/login")
        request.cliente = cliente
        request.cliente_correo = cliente.correo
        return vista(request, *args, **kwargs)

    return envoltura


def admin_requerido(vista):
    """Exige sesión de administrador; sin ella redirige a /admin/login."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        usuario = admin_actual(request)
        if usuario is None:
            return redirect("/admin/login")
        request.admin = usuario
        request.admin_correo = usuario.correo
        return vista(request, *args, **kwargs)

    return envoltura


def ruta_publica(ruta: str) -> bool:
    """Rutas que no exigen sesión (permitAll en Java, más /api/** por F1)."""
    if ruta in RUTAS_PUBLICAS or ruta.startswith("/static/"):
        return True
    return ruta.startswith("/api/") and ruta != "/api/obd2/conectar"
