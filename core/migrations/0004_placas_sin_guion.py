"""
Vuelve a aplicar la normalización de la 0002, que ahora también quita el guion de las
placas ("ABC-123" pasa a "ABC123"), en las bases que ya habían aplicado la 0002.
Es idempotente y deja sin tocar (con aviso) las placas que chocarían entre sí.
"""
from importlib import import_module

from django.db import migrations

normalizar_datos = import_module("core.migrations.0002_normalizar_datos").normalizar_datos


class Migration(migrations.Migration):
    dependencies = [("core", "0003_nivel_obligatorio")]

    operations = [migrations.RunPython(normalizar_datos, migrations.RunPython.noop)]
