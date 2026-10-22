"""
Lectura de parámetros y control de métodos HTTP con la semántica de Spring MVC.

parametro() equivale a @RequestParam: lee el formulario y la query string, y
responde 400 (BadRequest) si falta un parámetro obligatorio o un número no es válido.
"""
from functools import wraps

from django.core.exceptions import BadRequest

from core.errores import render_error
from core.utilidades import entero_java


def parametro(request, nombre: str, tipo: type = str, requerido: bool = True):
    if nombre in request.POST:
        valor = request.POST[nombre]
    elif nombre in request.GET:
        valor = request.GET[nombre]
    else:
        valor = None

    if valor is None:
        if requerido:
            raise BadRequest(f"Falta el parámetro obligatorio '{nombre}'.")
        return None
    if tipo is str:
        return valor

    # Spring convierte un número vacío en null: válido solo si el parámetro es opcional.
    if valor == "":
        if requerido:
            raise BadRequest(f"Falta el parámetro obligatorio '{nombre}'.")
        return None
    if tipo is int:
        numero = entero_java(valor, bits=64)
    elif tipo is float:
        numero = _decimal_java(valor)
    else:
        raise TypeError(f"Tipo de parámetro no soportado: {tipo}")
    if numero is None:
        raise BadRequest(f"El parámetro '{nombre}' no es un número válido.")
    return numero


def _decimal_java(valor: str) -> float | None:
    """Double.parseDouble: admite espacios alrededor, pero no guiones bajos."""
    if "_" in valor:
        return None
    try:
        return float(valor)
    except ValueError:
        return None


def metodos(*permitidos: str):
    """Limita la vista a ciertos métodos HTTP; "GET" incluye "HEAD", igual que @GetMapping."""
    aceptados = set(permitidos)
    if "GET" in aceptados:
        aceptados.add("HEAD")

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if request.method not in aceptados:
                respuesta = render_error(request, 405)
                respuesta["Allow"] = ", ".join(sorted(aceptados))
                return respuesta
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador
