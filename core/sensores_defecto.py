"""Sensores que se crean automáticamente al registrar un vehículo (web del cliente y API de la app)."""
from core.models import Sensor

# (nombre, tipo, tipo de daño) — igual que ApiController.SENSORES_POR_DEFECTO y VehiculoController.crear.
SENSORES_POR_DEFECTO = (
    ("Sensor de Flujo de Masa de Aire (MAF)", "MAF", "Falla en flujo de aire"),
    ("Sensor de Oxígeno (O2)", "O2", "Falla en mezcla"),
    ("Sensor de Temperatura del Refrigerante (ECT)", "ECT", "Sobrecalentamiento"),
    ("Sensor de Presión Absoluta del Colector (MAP)", "MAP", "Falla en presión"),
)


def crear_sensores_por_defecto(vehiculo) -> None:
    for nombre, tipo, tipo_dano in SENSORES_POR_DEFECTO:
        Sensor.objects.create(nombre_sensor=nombre, tipo_sensor=tipo, tipo_dano=tipo_dano, nivel=0, vehiculo=vehiculo)
