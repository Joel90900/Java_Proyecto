"""
Importación de un dump de phpMyAdmin (MySQL/MariaDB) a la base de Django.

Lee las sentencias INSERT del dump, conserva las claves primarias y los hashes,
normaliza placas, tipos de placa, modelo y niveles vacíos (lote A) y reinicia las secuencias de
PostgreSQL para que los registros nuevos continúen después de los importados.
"""
import re
from datetime import datetime

from django.core.management.color import no_style
from django.db import connection, models, transaction

from core.models import Alerta, Cliente, Lectura, Sensor, Usuario, Vehiculo
from core.normalizacion import normalizar_modelo, normalizar_placa, normalizar_tipo_placa

# Orden de inserción: primero las tablas referenciadas por claves foráneas.
TABLAS = [
    ("usuario", Usuario),
    ("cliente", Cliente),
    ("vehiculo", Vehiculo),
    ("sensores", Sensor),
    ("lecturas", Lectura),
    ("alertas", Alerta),
]

ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "0": "\0", "\\": "\\", "'": "'", '"': '"', "Z": "\x1a"}

_INSERT = re.compile(r"INSERT INTO\s+`(\w+)`\s*\(([^)]*)\)\s*VALUES\s*", re.IGNORECASE)
_ENTERO = re.compile(r"[+-]?\d+")


class ErrorImportacion(Exception):
    """El dump no se puede importar tal como está la base de datos."""


def parsear_valores(texto: str) -> list[list]:
    """Convierte "(1, 'a', NULL), (2, 'b', 3.5)" en [[1, "a", None], [2, "b", 3.5]]."""
    filas, _ = _leer_filas(texto, 0)
    return filas


def extraer_inserts(sql: str) -> list[tuple[str, list[str], list[list]]]:
    """Devuelve (tabla, columnas, filas) por cada INSERT del dump, en el orden en que aparecen."""
    inserts = []
    posicion = 0
    while True:
        coincidencia = _INSERT.search(sql, posicion)
        if coincidencia is None:
            return inserts
        tabla = coincidencia.group(1)
        columnas = [c.strip().strip("`") for c in coincidencia.group(2).split(",")]
        filas, posicion = _leer_filas(sql, coincidencia.end())
        inserts.append((tabla, columnas, filas))


def importar(sql: str, limpiar: bool, avisos: list[str] | None = None) -> dict[str, int]:
    """Importa los INSERT del dump y devuelve cuántas filas se importaron por tabla."""
    avisos = avisos if avisos is not None else []
    por_tabla: dict[str, list[tuple[list[str], list[list]]]] = {}
    for tabla, columnas, filas in extraer_inserts(sql):
        por_tabla.setdefault(tabla, []).append((columnas, filas))
    conocidas = {tabla for tabla, _ in TABLAS}
    for tabla in por_tabla:
        if tabla not in conocidas:
            avisos.append(f"Se ignora la tabla desconocida {tabla}.")

    with transaction.atomic():
        if limpiar:
            for _, modelo in reversed(TABLAS):
                modelo.objects.all().delete()
        else:
            for tabla, modelo in TABLAS:
                if modelo.objects.exists():
                    raise ErrorImportacion(f"La tabla {tabla} ya tiene datos; usa --limpiar para reemplazarlos.")

        conteos = {}
        for tabla, modelo in TABLAS:
            objetos = [
                _crear_objeto(modelo, columnas, fila, avisos)
                for columnas, filas in por_tabla.get(tabla, [])
                for fila in filas
            ]
            modelo.objects.bulk_create(objetos)
            conteos[tabla] = len(objetos)

        with connection.cursor() as cursor:
            for sentencia in connection.ops.sequence_reset_sql(no_style(), [m for _, m in TABLAS]):
                cursor.execute(sentencia)
    return conteos


def _crear_objeto(modelo, columnas: list[str], fila: list, avisos: list[str]):
    campos = {campo.column: campo for campo in modelo._meta.concrete_fields}
    datos = {}
    for columna, valor in zip(columnas, fila):
        campo = campos.get(columna)
        if campo is None:
            aviso = f"Se ignora la columna desconocida {modelo._meta.db_table}.{columna}."
            if aviso not in avisos:
                avisos.append(aviso)
            continue
        if isinstance(campo, models.DateTimeField) and isinstance(valor, str):
            valor = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")
        elif isinstance(campo, models.FloatField) and isinstance(valor, int):
            valor = float(valor)
        datos[campo.attname] = valor
    if modelo is Vehiculo:
        datos["placa"] = normalizar_placa(datos.get("placa"))
        if "tipo_placa" in datos:
            datos["tipo_placa"] = normalizar_tipo_placa(datos["tipo_placa"]) or datos["tipo_placa"]
        datos["modelo"] = normalizar_modelo(datos.get("modelo"))
    elif modelo is Sensor and datos.get("nivel") is None:
        datos["nivel"] = 0
    return modelo(**datos)


def _leer_filas(s: str, i: int) -> tuple[list[list], int]:
    """Lee tuplas "(…)" hasta un ";" fuera de comillas o hasta el final del texto."""
    filas = []
    while i < len(s):
        caracter = s[i]
        if caracter == ";":
            return filas, i + 1
        if caracter == "(":
            fila, i = _leer_fila(s, i + 1)
            filas.append(fila)
            continue
        i += 1  # comas, espacios y saltos de línea entre filas
    return filas, i


def _leer_fila(s: str, i: int) -> tuple[list, int]:
    valores = []
    while i < len(s):
        caracter = s[i]
        if caracter in " \t\r\n,":
            i += 1
        elif caracter == ")":
            return valores, i + 1
        elif caracter == "'":
            texto, i = _leer_cadena(s, i + 1)
            valores.append(texto)
        else:
            inicio = i
            while i < len(s) and s[i] not in ",)":
                i += 1
            valores.append(_convertir(s[inicio:i].strip()))
    raise ErrorImportacion("El dump tiene una fila sin cerrar.")


def _leer_cadena(s: str, i: int) -> tuple[str, int]:
    partes = []
    while i < len(s):
        caracter = s[i]
        if caracter == "\\" and i + 1 < len(s):
            partes.append(ESCAPES.get(s[i + 1], s[i + 1]))
            i += 2
        elif caracter == "'":
            if i + 1 < len(s) and s[i + 1] == "'":
                partes.append("'")
                i += 2
            else:
                return "".join(partes), i + 1
        else:
            partes.append(caracter)
            i += 1
    raise ErrorImportacion("El dump tiene una cadena sin cerrar.")


def _convertir(token: str):
    if token.upper() == "NULL":
        return None
    if _ENTERO.fullmatch(token):
        return int(token)
    return float(token)
