"""
API JSON para la app Android (equivale a ApiController y Obd2Controller).

Es pública y sin CSRF (F1): la app no maneja sesión y se identifica con el
correo. Las respuestas conservan las claves y su orden del JSON de Java.
"""
import random
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.auth import cifrar_contrasena, verificar_contrasena
from core.http import metodos, parametro
from core.models import Cliente, Sensor, Vehiculo
from core.sensores_defecto import crear_sensores_por_defecto
from core.utilidades import entero_java

FORMATO_PLACA = r"[A-Z]{3}-?[0-9]{3}"


def respuesta_json(datos: dict) -> JsonResponse:
    """JSON en UTF-8 sin escapar tildes, como Jackson."""
    return JsonResponse(datos, json_dumps_params={"ensure_ascii": False})


def cliente_info(c: Cliente) -> dict:
    return {
        "idCliente": c.id_cliente,
        "nombreCliente": c.nombre_cliente,
        "apellidoCliente": c.apellido_cliente,
        "correo": c.correo,
        "estado": c.estado,
    }


def sensor_info(s: Sensor) -> dict:
    return {
        "idSensor": s.id_sensor,
        "nombreSensor": s.nombre_sensor,
        "tipoSensor": s.tipo_sensor,
        "tipoDano": s.tipo_dano,
        "nivel": s.nivel,
    }


def anio_vehiculo(modelo: str | None) -> str:
    if modelo is None or modelo.strip() == "":
        return ""
    return modelo.split("-")[0]


def buscar_cliente(correo: str) -> Cliente | None:
    return Cliente.objects.filter(correo__iexact=correo).first()


# ---------------------------------------------------------------------------
# ApiController
# ---------------------------------------------------------------------------
@csrf_exempt
@metodos("POST")
def registrar(request):
    """Equivale a ApiController.registrar."""
    nombre = parametro(request, "nombre")
    apellido = parametro(request, "apellido")
    correo = parametro(request, "correo")
    contrasena = parametro(request, "contrasena")
    if buscar_cliente(correo) is not None:
        return respuesta_json({"ok": False, "mensaje": "El correo ya está registrado."})
    cliente = Cliente.objects.create(
        nombre_cliente=nombre.strip(),
        apellido_cliente=apellido.strip(),
        correo=correo.strip(),
        contrasena=cifrar_contrasena(contrasena),
        estado="activo",
    )
    return respuesta_json({"ok": True, "mensaje": "Cuenta creada correctamente.", "cliente": cliente_info(cliente)})


@csrf_exempt
@metodos("POST")
def login(request):
    """Equivale a ApiController.login (no crea sesión: la app guarda el correo)."""
    correo = parametro(request, "correo")
    contrasena = parametro(request, "contrasena")
    cliente = buscar_cliente(correo)
    if cliente is None or not verificar_contrasena(contrasena, cliente.contrasena):
        return respuesta_json({"ok": False, "mensaje": "Correo o contraseña incorrectos."})
    if cliente.estado == "bloqueado":
        return respuesta_json({"ok": False, "mensaje": "Tu cuenta está bloqueada. Contacta al administrador."})
    return respuesta_json({"ok": True, "mensaje": "Bienvenido.", "cliente": cliente_info(cliente)})


def datos_cliente_json(correo: str) -> dict:
    """Cuerpo de ApiController.datosCliente (también lo devuelve simularLecturas)."""
    cliente = buscar_cliente(correo)
    if cliente is None:
        return {"ok": False, "mensaje": "Cliente no encontrado."}
    vehiculos_json = []
    sensores_ok = advertencias = fallas = total_sensores = 0
    for v in Vehiculo.objects.filter(cliente=cliente):
        sensores_json = []
        for s in Sensor.objects.filter(vehiculo=v):
            if s.nivel < 40:
                sensores_ok += 1
            elif s.nivel < 70:
                advertencias += 1
            else:
                fallas += 1
            total_sensores += 1
            sensores_json.append(sensor_info(s))
        vehiculos_json.append({
            "idVehiculo": v.id_vehiculo,
            "nombreVehiculo": v.nombre_vehiculo,
            "marca": v.marca,
            "modelo": anio_vehiculo(v.modelo),
            "color": v.color,
            "placa": v.placa,
            "tipoPlaca": v.tipo_placa,
            "sensores": sensores_json,
        })
    return {
        "ok": True,
        "cliente": cliente_info(cliente),
        "vehiculos": vehiculos_json,
        "estadisticas": {
            "totalVehiculos": len(vehiculos_json),
            "totalSensores": total_sensores,
            "sensoresOk": sensores_ok,
            "advertencias": advertencias,
            "fallas": fallas,
        },
    }


@csrf_exempt
@metodos("GET")
def datos_cliente(request, correo):
    """Equivale a ApiController.datosCliente."""
    return respuesta_json(datos_cliente_json(correo))


@csrf_exempt
@metodos("POST")
def crear_vehiculo(request):
    """Equivale a ApiController.crearVehiculo."""
    correo = parametro(request, "correo")
    nombre_vehiculo = parametro(request, "nombreVehiculo")
    marca = parametro(request, "marca")
    modelo = parametro(request, "modelo")
    color = parametro(request, "color")
    placa = parametro(request, "placa")
    tipo_placa = parametro(request, "tipoPlaca")

    def error(mensaje):
        return respuesta_json({"ok": False, "mensaje": mensaje})

    cliente = buscar_cliente(correo)
    if cliente is None:
        return error("Cliente no encontrado.")
    if any(c.strip() == "" for c in (nombre_vehiculo, marca, modelo, color, placa, tipo_placa)):
        return error("Todos los campos son obligatorios.")
    anio = entero_java(modelo.strip())
    if anio is None:
        return error("El año debe ser un número válido.")
    if anio < 1990 or anio > 2030:
        return error("El año debe estar entre 1990 y 2030.")
    placa_normalizada = placa.upper().strip()
    if Vehiculo.objects.filter(placa__iexact=placa_normalizada).exists():
        return error("Ya existe un vehículo registrado con esa placa.")
    if not re.fullmatch(FORMATO_PLACA, placa_normalizada):
        return error("Formato de placa inválido. Ejemplo: ABC123 o ABC-123.")

    vehiculo = Vehiculo.objects.create(
        nombre_vehiculo=nombre_vehiculo.strip(),
        marca=marca.strip(),
        modelo=modelo.strip() + "-01-01",
        color=color.strip(),
        placa=placa_normalizada,
        tipo_placa=tipo_placa,
        cliente=cliente,
    )
    crear_sensores_por_defecto(vehiculo)
    return respuesta_json({"ok": True, "mensaje": "Vehículo registrado correctamente."})


@csrf_exempt
@metodos("POST")
def simular(request):
    """Equivale a ApiController.simularLecturas: suma a cada sensor un delta aleatorio entre -6 y 25."""
    correo = parametro(request, "correo")
    cliente = buscar_cliente(correo)
    if cliente is None:
        return respuesta_json({"ok": False, "mensaje": "Cliente no encontrado."})
    for v in Vehiculo.objects.filter(cliente=cliente):
        for s in Sensor.objects.filter(vehiculo=v):
            delta = random.randint(-6, 25)  # ThreadLocalRandom.nextInt(-6, 26)
            s.nivel = max(0, min(100, s.nivel + delta))
            s.save()
    return respuesta_json(datos_cliente_json(correo))
