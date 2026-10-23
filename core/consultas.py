"""
Consultas que reproducen cómo comparaba texto la base MySQL original.

Las tablas usaban la intercalación utf8mb4_general_ci: no distingue mayúsculas y
es PAD SPACE, es decir, ignora los espacios al final ('ana@ejemplo.com ' era igual a
'ana@ejemplo.com'). Los findByCorreo/findByPlaca de Java dependían de eso.
"""
from django.db.models.functions import RTrim, Upper


def igual_mysql(queryset, campo: str, valor: str | None):
    """Filtra por igualdad de texto ignorando mayúsculas y espacios finales, como MySQL."""
    buscado = (valor or "").rstrip(" ").upper()
    return queryset.annotate(_comparado_mysql=Upper(RTrim(campo))).filter(_comparado_mysql=buscado)
