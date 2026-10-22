"""Fábricas de datos de prueba compartidas por todas las apps."""
from functools import lru_cache

from core.auth import cifrar_contrasena
from core.models import Alerta, Cliente, Lectura, Sensor, Usuario, Vehiculo
from core.utilidades import ahora

CLAVE = "clave123"


@lru_cache(maxsize=1)
def hash_clave() -> str:
    """Hash bcrypt de CLAVE, calculado una sola vez (bcrypt es lento a propósito)."""
    return cifrar_contrasena(CLAVE)


def crear_usuario(correo="admin@autosen.com", nombre="Admin", rol="admin") -> Usuario:
    return Usuario.objects.create(nombre=nombre, correo=correo, contrasena=hash_clave(), rol=rol)


def crear_cliente(correo="joel@test.com", nombre="Joel", apellido="Moncaleano", estado="activo") -> Cliente:
    return Cliente.objects.create(
        nombre_cliente=nombre, apellido_cliente=apellido, correo=correo, contrasena=hash_clave(), estado=estado
    )


def crear_vehiculo(cliente, placa="ABC123", nombre="Onix", marca="Chevrolet", modelo="2020-01-01",
                   color="Negro", tipo_placa="particular", elm_mac=None) -> Vehiculo:
    return Vehiculo.objects.create(
        cliente=cliente, placa=placa, nombre_vehiculo=nombre, marca=marca, modelo=modelo,
        color=color, tipo_placa=tipo_placa, elm_mac=elm_mac,
    )


def crear_sensor(vehiculo, nivel=0, tipo="MAF", nombre="Sensor MAF", tipo_dano="Falla en flujo de aire",
                 estado=None) -> Sensor:
    return Sensor.objects.create(
        vehiculo=vehiculo, nivel=nivel, tipo_sensor=tipo, nombre_sensor=nombre, tipo_dano=tipo_dano, estado=estado
    )


def crear_lectura(id_vehiculo, nivel=0, valor=1.0, fecha=None, **campos) -> Lectura:
    datos = {"nombre_sensor": "S", "tipo_sensor": "T", **campos}
    return Lectura.objects.create(
        id_vehiculo=id_vehiculo, nivel=nivel, valor=valor, fecha_lectura=fecha or ahora(), **datos
    )


def crear_alerta(id_vehiculo, nivel=50, fecha=None, **campos) -> Alerta:
    datos = {"nombre_sensor": "S", "tipo_sensor": "T", "tipo": "advertencia", "mensaje": "m", "valor": 1.0, **campos}
    return Alerta.objects.create(id_vehiculo=id_vehiculo, nivel=nivel, fecha_alerta=fecha or ahora(), **datos)
