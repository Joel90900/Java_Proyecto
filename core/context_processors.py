from core.auth import admin_actual


def admin_correo(request):
    """Correo del administrador en sesión (sustituye a #authentication.name de Thymeleaf)."""
    correo = getattr(request, "admin_correo", None)
    if correo is None:
        usuario = admin_actual(request)
        correo = usuario.correo if usuario else ""
    return {"admin_correo": correo}
