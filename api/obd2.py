"""
Lógica OBD2: cálculo del nivel, simulación de lecturas y registro de alertas.

Copiado de Obd2Controller.java (calcularNivel, valorSimulado, unidadDe, redondear,
redondearDos) sin cambios de comportamiento. Ojo: calcular_nivel trata los valores
dentro del rango normal como desgaste y no tiene rangos para ECT ni MAP; se
conserva así a propósito (docs/PENDIENTES.md).
"""
import random

from core.models import Alerta
from core.patrones.observador import alerta_critica
from core.utilidades import ahora, double_java, redondear_java

# tipo: (mínimo normal, máximo normal). maxRango existía en Java pero nunca se usaba.
RANGOS = {
    "RPM": (600, 3000),
    "VELOCIDAD": (0, 100),
    "TEMP": (80, 100),
    "MAF": (2, 8),
    "O2": (0.1, 0.9),
    "OIL": (1, 5),
    "FUEL": (20, 80),
}
RANGO_POR_DEFECTO = (0, 100)

UNIDADES = {"RPM": "rpm", "VELOCIDAD": "km/h", "TEMP": "°C", "ECT": "°C", "MAF": "g/s", "O2": "V", "OIL": "bar",
            "FUEL": "%"}


def calcular_nivel(tipo_sensor: str, valor: float) -> int:
    minimo, maximo = RANGOS.get(tipo_sensor, RANGO_POR_DEFECTO)
    if valor <= minimo:
        return 0
    if valor >= maximo:
        return 100
    return redondear_java((valor - minimo) / (maximo - minimo) * 100)


def redondear(d: float) -> float:
    return redondear_java(d * 10.0) / 10.0


def redondear_dos(d: float) -> float:
    return redondear_java(d * 100.0) / 100.0


def valor_simulado(tipo: str | None) -> float:
    """Valor aleatorio por tipo de sensor (botón "Conectar Bluetooth"); random.random() equivale a Math.random()."""
    match tipo or "":
        case "MAF":
            return redondear(2 + random.random() * 10)
        case "O2":
            return redondear_dos(0.1 + random.random() * 1.1)
        case "ECT":
            return redondear(75 + random.random() * 55)
        case "MAP":
            return redondear_dos(0.5 + random.random() * 0.7)
        case "RPM":
            return float(redondear_java(650 + random.random() * 3800))
        case "VELOCIDAD":
            return float(redondear_java(random.random() * 120))
        case "TEMP":
            return redondear(75 + random.random() * 55)
        case "OIL":
            return redondear_dos(1 + random.random() * 5)
        case "FUEL":
            return float(redondear_java(15 + random.random() * 80))
        case _:
            return redondear(random.random() * 100)


def unidad_de(tipo: str | None) -> str:
    return UNIDADES.get(tipo or "", "")


def estado_por_nivel(nivel: int) -> str:
    return "OK" if nivel < 40 else "ADVERTENCIA" if nivel < 70 else "FALLA"


def crear_alerta_si_corresponde(id_vehiculo: int, nombre_sensor: str, tipo_sensor: str, valor: float, nivel: int,
                                sufijo_unidad: str) -> Alerta | None:
    """Con nivel >= 40 registra la alerta y notifica a los observadores (alerta_critica)."""
    if nivel < 40:
        return None
    detalle = f"{nombre_sensor}: nivel {nivel}% ({double_java(valor)}{sufijo_unidad})."
    alerta = Alerta.objects.create(
        id_vehiculo=id_vehiculo,
        nombre_sensor=nombre_sensor,
        tipo_sensor=tipo_sensor,
        valor=valor,
        nivel=nivel,
        tipo="falla" if nivel >= 70 else "advertencia",
        mensaje=("Falla crítica en " if nivel >= 70 else "Advertencia en ") + detalle,
        leida=0,
        fecha_alerta=ahora(),
    )
    alerta_critica.send(sender=crear_alerta_si_corresponde, alerta=alerta)
    return alerta
