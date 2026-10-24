"""
Normaliza los datos guardados (lote A): placas en mayúsculas, sin espacios y sin guion,
tipos de placa canónicos, modelo como "AAAA-01-01" y sensores sin nivel con nivel 0.

Si dos placas quedarían iguales al normalizarlas (p. ej. "ABC-123" y "abc123"), se dejan
como están y se avisa en la consola, para que alguien decida cuál corregir.

El cambio de esquema (nivel obligatorio, admin desvinculable) va en la 0003: en
PostgreSQL no conviene modificar filas y alterar la misma tabla en una sola transacción.
"""
from collections import defaultdict

from django.db import migrations

from core.normalizacion import normalizar_modelo, normalizar_placa, normalizar_tipo_placa


def normalizar_datos(apps, schema_editor):
    Vehiculo = apps.get_model("core", "Vehiculo")
    Sensor = apps.get_model("core", "Sensor")
    vehiculos = list(Vehiculo.objects.all())
    por_placa = defaultdict(list)
    for vehiculo in vehiculos:
        if vehiculo.placa is not None:
            por_placa[normalizar_placa(vehiculo.placa)].append(vehiculo)
    chocan = {placa: grupo for placa, grupo in por_placa.items() if len(grupo) > 1}
    for placa, grupo in chocan.items():
        originales = ", ".join(f"{v.pk}: {v.placa!r}" for v in grupo)
        print(f"Aviso: estas placas quedarían iguales ({placa}) y se dejan sin normalizar: {originales}")
    for vehiculo in vehiculos:
        placa = normalizar_placa(vehiculo.placa)
        nuevos = (
            vehiculo.placa if placa in chocan else placa,
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
