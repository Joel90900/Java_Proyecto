"""Vistas del panel de administración (equivalen a AdminController)."""
from django.shortcuts import redirect, render

from core.auth import cerrar_sesion_admin, iniciar_sesion_admin, verificar_contrasena
from core.http import metodos
from core.models import Usuario


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
