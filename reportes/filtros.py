"""
Filtros y orden de los reportes (equivalen a los helpers de ReporteController).

Los usan la vista /admin/reportes-filtrado, la exportación a Excel y el PDF general,
así que los tres aplican exactamente los mismos criterios (F5).
"""
import unicodedata

from core.http import parametro
from core.patrones.fabrica import EstadoSensorStrategyFactory, TipoEstado

STRATEGY_FILTRO = EstadoSensorStrategyFactory.crear(TipoEstado.FILTRO)


def _con_valor(texto: str | None) -> bool:
    """texto != null && !texto.isBlank()"""
    return texto is not None and texto.strip() != ""


def _nr(texto: str | None) -> str:
    return "" if texto is None else texto


def nz_nivel(sensor) -> int:
    return 0 if sensor.nivel is None else sensor.nivel


def sin_tildes(texto: str | None) -> str:
    """Minúsculas y sin marcas diacríticas: "Público" y "publico" quedan iguales."""
    descompuesto = unicodedata.normalize("NFKD", _nr(texto))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def normalizar_rango(nivel_min: int | None, nivel_max: int | None) -> tuple[int | None, int | None]:
    """El nivel mínimo no debe superar al máximo: si llegan al revés, se intercambian."""
    if nivel_min is not None and nivel_max is not None and nivel_min > nivel_max:
        return nivel_max, nivel_min
    return nivel_min, nivel_max


def filtrar_sensores(sensores, estado_sensor, tipo_sensor, nivel_min, nivel_max) -> list:
    """Equivale a ReporteController.filtrarSensores."""
    resultado = []
    for s in sensores:
        if _con_valor(estado_sensor) and estado_sensor.lower() != STRATEGY_FILTRO.clasificar(s.nivel):
            continue
        if _con_valor(tipo_sensor) and tipo_sensor != s.tipo_sensor:
            continue
        if nivel_min is not None and (s.nivel is None or s.nivel < nivel_min):
            continue
        if nivel_max is not None and (s.nivel is None or s.nivel > nivel_max):
            continue
        resultado.append(s)
    return resultado


def _coincide(q: str, cliente, vehiculos) -> bool:
    """Equivale a ReporteController.coincide: busca en nombre, apellido, correo, placa y nombre del vehículo."""
    ql = q.lower()
    texto = f"{_nr(cliente.nombre_cliente)} {_nr(cliente.apellido_cliente)} {_nr(cliente.correo)}".lower()
    if ql in texto:
        return True
    return any(ql in _nr(v.placa).lower() or ql in _nr(v.nombre_vehiculo).lower() for v in vehiculos)


def filtrar_clientes(clientes, q, estado_cliente, marca, tipo_placa) -> list:
    """Equivale a ReporteController.filtrarClientes, más el filtro por tipo de placa (F5)."""
    resultado = []
    for c in clientes:
        if _con_valor(estado_cliente) and (c.estado is None or estado_cliente.lower() != c.estado.lower()):
            continue
        vehiculos = list(c.vehiculos.all())
        if _con_valor(marca) and not any(v.marca is not None and marca.lower() == v.marca.lower() for v in vehiculos):
            continue
        if _con_valor(tipo_placa) and not any(sin_tildes(tipo_placa) == sin_tildes(v.tipo_placa) for v in vehiculos):
            continue
        if _con_valor(q) and not _coincide(q, c, vehiculos):
            continue
        resultado.append(c)
    return resultado


def peso_estado(estado: str | None) -> int:
    return {"falla": 2, "advertencia": 1}.get(estado or "", 0)


def ordenar_sensores(sensores: list, ordenar_por: str | None) -> list:
    """Equivale a ReporteController.comparadorSensores (orden estable, como List.sort de Java)."""
    criterio = "nombre" if ordenar_por is None else ordenar_por
    if criterio == "nivel":
        return sorted(sensores, key=nz_nivel, reverse=True)
    if criterio == "estado":
        return sorted(sensores, key=lambda s: peso_estado(STRATEGY_FILTRO.clasificar(s.nivel)))

    def nombre_cliente(s):
        if s.vehiculo is not None and s.vehiculo.cliente is not None:
            return _nr(s.vehiculo.cliente.nombre_cliente)
        return ""

    return sorted(sensores, key=nombre_cliente)


def parametros_filtro(request) -> dict:
    """Lee los filtros del formulario de reportes; los niveles vacíos significan "sin filtro"."""
    nivel_min, nivel_max = normalizar_rango(parametro(request, "nivelMin", int, requerido=False),
                                            parametro(request, "nivelMax", int, requerido=False))
    datos = {nombre: parametro(request, nombre, requerido=False)
             for nombre in ("q", "estadoCliente", "estadoSensor", "tipoSensor", "marca", "tipoPlaca", "ordenarPor")}
    datos.update({"nivelMin": nivel_min, "nivelMax": nivel_max})
    return datos
