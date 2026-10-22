"""Vistas de la web del cliente (equivalen a AuthController, DashboardController y VehiculoController)."""
from django.shortcuts import redirect, render

from core.auth import cerrar_sesion_cliente, cifrar_contrasena, iniciar_sesion_cliente, verificar_contrasena
from core.http import metodos, parametro
from core.models import Cliente


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
