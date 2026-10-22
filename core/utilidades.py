"""
Equivalencias de comportamiento Java → Python.

El código migrado debe usar estas funciones en lugar de las de Python cuando
reproduce una operación Java, porque la semántica difiere en casos borde
(redondeo de .5, espacios en números, null en concatenaciones, formato de fechas).
"""
import math
import re
from datetime import datetime
from decimal import Decimal

_ENTERO = re.compile(r"[+-]?[0-9]+")


def redondear_java(x: float) -> int:
    """Math.round(x): redondea .5 hacia arriba (round() de Python redondea al par)."""
    return math.floor(x + 0.5)


def entero_java(s: str, bits: int = 32) -> int | None:
    """
    Integer.parseInt(s) (bits=32) o Long.parseLong(s) (bits=64).

    Devuelve None donde Java lanzaría NumberFormatException: espacios,
    decimales, guiones bajos, texto vacío o un valor fuera de rango.
    """
    if s is None or not _ENTERO.fullmatch(s):
        return None
    valor = int(s)
    limite = 2 ** (bits - 1)
    if not -limite <= valor < limite:
        return None
    return valor


def texto_java(valor) -> str:
    """String.valueOf(valor): un null de Java se escribe "null"."""
    return "null" if valor is None else str(valor)


def double_java(valor: float) -> str:
    """Double.toString(valor): notación decimal entre 1e-3 y 1e7, científica fuera de ese rango."""
    valor = float(valor)
    if math.isnan(valor):
        return "NaN"
    if math.isinf(valor):
        return "Infinity" if valor > 0 else "-Infinity"
    if valor == 0 or 1e-3 <= abs(valor) < 1e7:
        return repr(valor)
    signo, digitos, exponente = Decimal(repr(abs(valor))).normalize().as_tuple()
    exponente_cientifico = len(digitos) - 1 + exponente
    cifras = "".join(str(d) for d in digitos)
    mantisa = cifras[0] + "." + (cifras[1:] or "0")
    return ("-" if valor < 0 else "") + f"{mantisa}E{exponente_cientifico}"


def fecha_java(dt: datetime | None) -> str:
    """String.valueOf(LocalDateTime): omite los segundos cuando son cero; "null" si no hay fecha."""
    if dt is None:
        return "null"
    texto = dt.strftime("%Y-%m-%dT%H:%M")
    if dt.second or dt.microsecond:
        texto += dt.strftime(":%S")
        if dt.microsecond:
            texto += f".{dt.microsecond:06d}".rstrip("0")
    return texto


def ahora() -> datetime:
    """LocalDateTime.now() guardado en un TIMESTAMP de MySQL: hora local sin microsegundos."""
    return datetime.now().replace(microsecond=0)
