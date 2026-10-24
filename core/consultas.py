"""
Consultas que reproducen cómo comparaba texto la base MySQL original.

Las tablas usaban la intercalación utf8mb4_general_ci: no distingue mayúsculas y
es PAD SPACE, es decir, ignora los espacios al final ('ana@ejemplo.com ' era igual a
'ana@ejemplo.com'). Los findByCorreo/findByPlaca de Java dependían de eso.
"""
from django.db.models.functions import RTrim, Upper

from core.normalizacion import normalizar_placa


def igual_mysql(queryset, campo: str, valor: str | None):
    """Filtra por igualdad de texto ignorando mayúsculas y espacios finales, como MySQL."""
    buscado = (valor or "").rstrip(" ").upper()
    return queryset.annotate(_comparado_mysql=Upper(RTrim(campo))).filter(_comparado_mysql=buscado)


def placa_duplicada(placa: str, vehiculo=None) -> bool:
    """Otro vehículo ya tiene esa placa. Al editar (vehiculo dado) no se compara si la placa no cambió:
    tras normalizar los datos pueden quedar dos vehículos con la misma placa y ninguno se podría editar."""
    from core.models import Vehiculo

    if vehiculo is not None and vehiculo.placa is not None and normalizar_placa(vehiculo.placa) == normalizar_placa(placa):
        return False
    otros = Vehiculo.objects.all() if vehiculo is None else Vehiculo.objects.exclude(pk=vehiculo.pk)
    return igual_mysql(otros, "placa", placa).exists()
