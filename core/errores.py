"""
Páginas de error (equivale a CustomErrorController de Java).

Todas usan templates/error.html con status, error (frase HTTP) y message.
"""
from http import HTTPStatus

from django.shortcuts import render

MENSAJES = {
    404: "El recurso solicitado no fue encontrado.",
    403: "No tienes permisos para acceder aquí.",
    500: "Error interno del servidor.",
}


def render_error(request, status: int, http_status: int | None = None):
    contexto = {
        "status": status,
        "error": HTTPStatus(status).phrase,
        "message": MENSAJES.get(status, "Ocurrió un error inesperado."),
    }
    return render(request, "error.html", contexto, status=http_status or status)


def error_400(request, exception=None):
    return render_error(request, 400)


def error_403(request, exception=None):
    return render_error(request, 403)


def error_404(request, exception=None):
    return render_error(request, 404)


def error_500(request):
    return render_error(request, 500)


def pagina_error(request):
    """GET /error: como en Java, muestra la página de error 500 con estado HTTP 200."""
    return render_error(request, 500, http_status=200)
