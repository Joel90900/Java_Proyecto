"""
API JSON para la app Android (equivale a ApiController y Obd2Controller).

Es pública y sin CSRF (F1): la app no maneja sesión y se identifica con el
correo. Las respuestas conservan las claves y su orden del JSON de Java.
"""
import random

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.obd2 import calcular_nivel, crear_alerta_si_corresponde, estado_por_nivel, unidad_de, valor_simulado
from core.auth import cifrar_contrasena, cliente_requerido, verificar_contrasena
from core.consultas import igual_mysql
from core.http import metodos, parametro
from core.models import Alerta, Cliente, Lectura, Sensor, Vehiculo
from core.normalizacion import normalizar_modelo, normalizar_placa, normalizar_tipo_placa
from core.sensores_defecto import crear_sensores_por_defecto
from core.utilidades import ahora, fecha_java
from core.validaciones import validar_largos, validar_persona, validar_vehiculo



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
    return igual_mysql(Cliente.objects.all(), "correo", correo).first()


# ---------------------------------------------------------------------------
# ApiController
# ---------------------------------------------------------------------------
@csrf_exempt
@metodos("POST")
def registrar(request):
    """Equivale a ApiController.registrar, con las validaciones comunes (lote A)."""
    nombre = parametro(request, "nombre").strip()
    apellido = parametro(request, "apellido").strip()
    correo = parametro(request, "correo").strip()
    contrasena = parametro(request, "contrasena")
    error = validar_persona([nombre, apellido], correo, contrasena) or validar_largos(
        Cliente, {"nombre_cliente": nombre, "apellido_cliente": apellido, "correo": correo})
    if error is None and buscar_cliente(correo) is not None:
        error = "El correo ya está registrado."
    if error:
        return respuesta_json({"ok": False, "mensaje": error})
    cliente = Cliente.objects.create(
        nombre_cliente=nombre,
        apellido_cliente=apellido,
        correo=correo,
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
    """Equivale a ApiController.crearVehiculo, con las validaciones comunes (lote A)."""
    correo = parametro(request, "correo")
    nombre_vehiculo = parametro(request, "nombreVehiculo").strip()
    marca = parametro(request, "marca").strip()
    modelo = parametro(request, "modelo").strip()
    color = parametro(request, "color").strip()
    placa = normalizar_placa(parametro(request, "placa"))
    tipo_placa = parametro(request, "tipoPlaca")

    cliente = buscar_cliente(correo)
    error = "Cliente no encontrado." if cliente is None else validar_vehiculo(
        nombre_vehiculo, marca, modelo, color, placa, tipo_placa) or validar_largos(
        Vehiculo, {"nombre_vehiculo": nombre_vehiculo, "marca": marca, "color": color})
    if error is None and igual_mysql(Vehiculo.objects.all(), "placa", placa).exists():
        error = "Ya existe un vehículo registrado con esa placa."
    if error:
        return respuesta_json({"ok": False, "mensaje": error})

    vehiculo = Vehiculo.objects.create(
        nombre_vehiculo=nombre_vehiculo,
        marca=marca,
        modelo=normalizar_modelo(modelo),
        color=color,
        placa=placa,
        tipo_placa=normalizar_tipo_placa(tipo_placa),
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


# ---------------------------------------------------------------------------
# Obd2Controller
# ---------------------------------------------------------------------------
def lectura_json(lectura: Lectura, con_id: bool = True) -> dict:
    datos = {"idLectura": lectura.id_lectura} if con_id else {}
    datos.update({
        "nombreSensor": lectura.nombre_sensor,
        "tipoSensor": lectura.tipo_sensor,
        "valor": lectura.valor,
        "unidad": lectura.unidad,
        "nivel": lectura.nivel,
        "estado": lectura.estado,
        "fechaLectura": fecha_java(lectura.fecha_lectura),
    })
    return datos


@csrf_exempt
@metodos("POST")
def guardar_lectura(request):
    """Equivale a Obd2Controller.guardarLectura (lecturas reales del ELM327 enviadas por la app)."""
    id_vehiculo = parametro(request, "idVehiculo", int)
    nombre_sensor = parametro(request, "nombreSensor")
    tipo_sensor = parametro(request, "tipoSensor")
    valor = parametro(request, "valor", float)
    unidad = parametro(request, "unidad", requerido=False)
    if not Vehiculo.objects.filter(pk=id_vehiculo).exists():
        return respuesta_json({"ok": False, "mensaje": "Vehículo no encontrado."})

    nivel = calcular_nivel(tipo_sensor, valor)
    lectura = Lectura.objects.create(
        id_vehiculo=id_vehiculo,
        nombre_sensor=nombre_sensor,
        tipo_sensor=tipo_sensor,
        valor=valor,
        unidad="" if unidad is None else unidad,
        nivel=nivel,
        estado=estado_por_nivel(nivel),
        fecha_lectura=ahora(),
    )
    crear_alerta_si_corresponde(id_vehiculo, nombre_sensor, tipo_sensor, valor, nivel,
                                "" if unidad is None else " " + unidad)
    return respuesta_json({"ok": True, "mensaje": "Lectura registrada.", "idLectura": lectura.id_lectura,
                           "nivel": nivel, "estado": lectura.estado})


@csrf_exempt
@metodos("GET", "POST")
def elm(request, id):
    """Equivale a Obd2Controller.guardarElm (POST) y obtenerElm (GET)."""
    if request.method == "POST":
        elm_mac = parametro(request, "elmMac")
        vehiculo = Vehiculo.objects.filter(pk=id).first()
        if vehiculo is None:
            return respuesta_json({"ok": False, "mensaje": "Vehículo no encontrado."})
        vehiculo.elm_mac = elm_mac
        vehiculo.save()
        return respuesta_json({"ok": True, "mensaje": "ELM327 guardado para reconexión futura.", "elmMac": elm_mac})

    vehiculo = Vehiculo.objects.filter(pk=id).first()
    if vehiculo is None:
        return respuesta_json({"ok": False, "mensaje": "Vehículo no encontrado."})
    sin_elm = vehiculo.elm_mac is None or vehiculo.elm_mac.strip() == ""
    return respuesta_json({
        "ok": True,
        "idVehiculo": id,
        "elmMac": vehiculo.elm_mac,
        "conectado": False,
        "mensaje": "No hay un ELM327 asociado a este vehículo." if sin_elm
        else "ELM327 registrado. La conexión Bluetooth debe realizarse desde Android.",
    })


@csrf_exempt
@metodos("GET")
def historial(request, id_vehiculo):
    """Equivale a Obd2Controller.historial: todas las lecturas del vehículo, de la más reciente a la más antigua."""
    lecturas = Lectura.objects.filter(id_vehiculo=id_vehiculo).order_by("-id_lectura")
    return respuesta_json({"ok": True, "lecturas": [lectura_json(lectura) for lectura in lecturas]})


@csrf_exempt
@metodos("GET")
def alertas(request, id_vehiculo):
    """Equivale a Obd2Controller.alertas: mira solo las 50 alertas más recientes de todo el sistema."""
    recientes = Alerta.objects.order_by("-id_alerta")[:50]
    return respuesta_json({"ok": True, "alertas": [
        {
            "idAlerta": a.id_alerta,
            "nombreSensor": a.nombre_sensor,
            "tipoSensor": a.tipo_sensor,
            "valor": a.valor,
            "nivel": a.nivel,
            "tipo": a.tipo,
            "mensaje": a.mensaje,
            "leida": a.leida is not None and a.leida == 1,
            "fechaAlerta": fecha_java(a.fecha_alerta),
        }
        for a in recientes if a.id_vehiculo == id_vehiculo
    ]})


@csrf_exempt
@metodos("GET")
def ultima(request, id_vehiculo):
    """Equivale a Obd2Controller.ultima: las 30 lecturas más recientes del vehículo."""
    lecturas = Lectura.objects.filter(id_vehiculo=id_vehiculo).order_by("-id_lectura")[:30]
    return respuesta_json({"ok": True, "lecturas": [lectura_json(lectura, con_id=False) for lectura in lecturas]})


@csrf_exempt
@cliente_requerido
@metodos("POST")
def conectar(request):
    """
    Equivale a Obd2Controller.conectar (botón "Conectar Bluetooth" del dashboard web).

    Simula el escáner ELM327: toma el primer vehículo del cliente, genera una lectura
    aleatoria por sensor, la guarda y devuelve la telemetría.
    """
    vehiculos = list(Vehiculo.objects.filter(cliente=request.cliente))
    if not vehiculos:
        return respuesta_json({"ok": False, "conectado": False,
                               "mensaje": "Primero registra un vehículo para poder conectar el escáner ELM327."})
    v = vehiculos[0]
    sin_elm = v.elm_mac is None or v.elm_mac.strip() == ""
    respuesta = {
        "ok": True,
        "conectado": True,
        "idVehiculo": v.id_vehiculo,
        "vehiculo": (v.nombre_vehiculo or "") + " " + (v.placa or ""),
        "elmMac": "ELM327-SIM-" + (v.placa or "") if sin_elm else v.elm_mac,
        "mensaje": "Escáner ELM327 conectado por Bluetooth. Recibiendo datos del vehículo en tiempo real.",
    }
    lecturas = []
    for s in Sensor.objects.filter(vehiculo=v):
        tipo = s.tipo_sensor
        valor = valor_simulado(tipo)
        unidad = unidad_de(tipo)
        nivel = calcular_nivel(tipo, valor)
        estado = estado_por_nivel(nivel)
        Lectura.objects.create(id_vehiculo=v.id_vehiculo, nombre_sensor=s.nombre_sensor, tipo_sensor=tipo, valor=valor,
                               unidad=unidad, nivel=nivel, estado=estado, fecha_lectura=ahora())
        crear_alerta_si_corresponde(v.id_vehiculo, s.nombre_sensor, tipo, valor, nivel, " " + unidad)
        lecturas.append({"nombreSensor": s.nombre_sensor, "tipoSensor": tipo, "valor": valor, "unidad": unidad,
                         "nivel": nivel, "estado": estado})
    respuesta["lecturas"] = lecturas
    return respuesta_json(respuesta)
