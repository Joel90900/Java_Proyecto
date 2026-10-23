"""
Normaliza los datos guardados (lote A): placas en mayúsculas y sin espacios, tipos
de placa canónicos, modelo como "AAAA-01-01" y sensores sin nivel con nivel 0.

El cambio de esquema (nivel obligatorio, admin desvinculable) va en la 0003: en
PostgreSQL no conviene modificar filas y alterar la misma tabla en una sola transacción.
"""
from django.db import migrations

from core.normalizacion import normalizar_modelo, normalizar_placa, normalizar_tipo_placa


def normalizar_datos(apps, schema_editor):
    Vehiculo = apps.get_model("core", "Vehiculo")
    Sensor = apps.get_model("core", "Sensor")
    for vehiculo in Vehiculo.objects.all():
        nuevos = (
            normalizar_placa(vehiculo.placa),
            normalizar_tipo_placa(vehiculo.tipo_placa) or vehiculo.tipo_placa,
            normalizar_modelo(vehiculo.modelo),
        )
        if nuevos != (vehiculo.placa, vehiculo.tipo_placa, vehiculo.modelo):
            vehiculo.placa, vehiculo.tipo_placa, vehiculo.modelo = nuevos
            vehiculo.save(update_fields=["placa", "tipo_placa", "modelo"])
    Sensor.objects.filter(nivel__isnull=True).update(nivel=0)


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [migrations.RunPython(normalizar_datos, migrations.RunPython.noop)]
