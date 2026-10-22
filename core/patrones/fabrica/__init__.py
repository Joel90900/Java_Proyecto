"""
GoF – Simple Factory / Factory Method.

Encapsula la creación de las estrategias de clasificación de estado: el cliente
indica el tipo y la fábrica decide qué estrategia concreta entregar.
"""
import enum

from core.patrones.estrategia import EstadoSensorFiltroStrategy, EstadoSensorReporteStrategy, EstadoSensorStrategy


class TipoEstado(enum.Enum):
    """Tipos de estrategia que la fábrica puede crear."""

    REPORTE = "REPORTE"  # Etiquetas cortas para PDF/reportes: OK, ADVERTENCIA, FALLA
    FILTRO = "FILTRO"  # Etiquetas de auditoría/filtros: optimo, advertencia, falla


class EstadoSensorStrategyFactory:
    @staticmethod
    def crear(tipo: TipoEstado) -> EstadoSensorStrategy:
        match tipo:
            case TipoEstado.REPORTE:
                return EstadoSensorReporteStrategy.get_instancia()
            case TipoEstado.FILTRO:
                return EstadoSensorFiltroStrategy.get_instancia()
        raise ValueError(f"Tipo de estado desconocido: {tipo}")
