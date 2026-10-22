"""
Filtros de plantilla que reemplazan las expresiones con lógica de las plantillas Thymeleaf.

Uso: {{ s.nivel|estado_nivel:"FALLA,ADVERTENCIA,OK" }} devuelve la etiqueta que
corresponde al nivel (>= 70 falla, >= 40 advertencia, si no ok; None cuenta como ok).
"""
from django import template

from core.utilidades import double_java, texto_java

register = template.Library()


@register.filter
def java(valor) -> str:
    """Concatenación de Thymeleaf/SpEL: un null se escribe "null" (Django escribiría "None")."""
    return texto_java(valor)


@register.filter
def multiplicar(a, b) -> str:
    """Producto con el formato de un double de Java (p. ej. el retardo de animación iter.index * 0.08)."""
    return double_java(float(a) * float(b))


@register.filter
def estado_nivel(nivel, etiquetas: str) -> str:
    falla, advertencia, ok = etiquetas.split(",")
    if nivel is not None and nivel >= 70:
        return falla
    if nivel is not None and nivel >= 40:
        return advertencia
    return ok


@register.filter
def estado_informe(obj, etiquetas: str) -> str:
    """Variante de los informes imprimibles: también consulta el campo estado ('falla'/'advertencia')."""
    falla, advertencia, ok = etiquetas.split(",")
    nivel = getattr(obj, "nivel", None)
    estado = (getattr(obj, "estado", None) or "").lower()
    if (nivel is not None and nivel >= 70) or estado == "falla":
        return falla
    if (nivel is not None and nivel >= 40) or estado == "advertencia":
        return advertencia
    return ok
