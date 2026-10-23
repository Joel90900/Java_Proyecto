"""
Normalización de datos de vehículos: placa, tipo de placa y modelo (año).

La usan la migración de datos, el importador y las validaciones, para que lo
guardado sea siempre igual venga de la web, del panel, de la API o de un dump.
"""
import re
import unicodedata

TIPOS_PLACA = ("particular", "publico", "oficial", "diplomatico")


def sin_tildes(texto: str | None) -> str:
    """Minúsculas y sin marcas diacríticas: "Público" y "publico" quedan iguales."""
    descompuesto = unicodedata.normalize("NFKD", "" if texto is None else texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def normalizar_placa(placa: str | None) -> str | None:
    """Sin espacios alrededor y en mayúsculas."""
    return None if placa is None else placa.strip().upper()


def normalizar_tipo_placa(tipo: str | None) -> str | None:
    """Uno de TIPOS_PLACA sin importar mayúsculas, tildes ni espacios; None si no es ninguno."""
    if tipo is None:
        return None
    canonico = sin_tildes(tipo.strip())
    return canonico if canonico in TIPOS_PLACA else None


def normalizar_modelo(modelo: str | None) -> str | None:
    """Un año "2020" se guarda como "2020-01-01"; cualquier otro valor se deja igual."""
    if modelo is not None and re.fullmatch(r"\d{4}", modelo):
        return f"{modelo}-01-01"
    return modelo
