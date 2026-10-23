"""
Reglas de validación comunes a la web del cliente, el panel y la API (lote A).

Cada función devuelve None si todo está bien o el mensaje de error a mostrar.
Los textos llegan ya recortados y la placa ya normalizada (core.normalizacion).
El duplicado (correo o placa) lo comprueba quien llama, porque necesita la base de datos.
"""
import re

from core.normalizacion import normalizar_tipo_placa
from core.utilidades import entero_java

OBLIGATORIOS = "Todos los campos son obligatorios."
FORMATO_CORREO = r"[^@\s]+@[^@\s]+\.[^@\s]+"
FORMATO_PLACA = r"[A-Z]{3}-?[0-9]{3}"
LARGO_MINIMO_CONTRASENA = 6
ANIO_MINIMO, ANIO_MAXIMO = 1990, 2030


def _vacio(texto: str | None) -> bool:
    return texto is None or texto == ""


def validar_persona(obligatorios: list[str], correo: str, contrasena: str | None,
                    contrasena_obligatoria: bool = True) -> str | None:
    """Clientes ([nombre, apellido]) y administradores ([nombre])."""
    if any(_vacio(campo) for campo in obligatorios) or _vacio(correo):
        return OBLIGATORIOS
    if contrasena_obligatoria and _vacio(contrasena):
        return OBLIGATORIOS
    if not re.fullmatch(FORMATO_CORREO, correo):
        return "El correo no tiene un formato válido."
    if not _vacio(contrasena) and len(contrasena) < LARGO_MINIMO_CONTRASENA:
        return "La contraseña debe tener al menos 6 caracteres."
    return None


def validar_vehiculo(nombre: str, marca: str, modelo: str | None, color: str, placa: str, tipo_placa: str,
                     modelo_obligatorio: bool = True) -> str | None:
    if any(_vacio(campo) for campo in (nombre, marca, color, placa, tipo_placa)):
        return OBLIGATORIOS
    if modelo_obligatorio and _vacio(modelo):
        return OBLIGATORIOS
    if not _vacio(modelo):
        anio = entero_java(modelo)
        if anio is None:
            return "El año debe ser un número válido."
        if anio < ANIO_MINIMO or anio > ANIO_MAXIMO:
            return "El año debe estar entre 1990 y 2030."
    if not re.fullmatch(FORMATO_PLACA, placa):
        return "Formato de placa inválido. Ejemplo: ABC123 o ABC-123."
    if normalizar_tipo_placa(tipo_placa) is None:
        return "Selecciona un tipo de placa válido."
    return None
