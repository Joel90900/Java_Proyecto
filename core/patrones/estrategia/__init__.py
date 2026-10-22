"""
GoF – Strategy.

Familia de algoritmos intercambiables para clasificar el nivel de un sensor.
El contexto (ClasificadorEstadoSensor) delega en la estrategia configurada.
"""
from abc import ABC, abstractmethod

from core.patrones.singleton import UmbralesReporte


class EstadoSensorStrategy(ABC):
    """Contrato de las estrategias de clasificación de estado de un sensor."""

    @abstractmethod
    def clasificar(self, nivel: int | None) -> str:
        """Clasifica el nivel (porcentaje de desgaste/lectura, puede ser None) en un estado legible."""


class EstadoSensorReporteStrategy(EstadoSensorStrategy):
    """Etiquetas cortas para PDF/reportes: "OK", "ADVERTENCIA", "FALLA"."""

    _instancia = None

    @classmethod
    def get_instancia(cls) -> "EstadoSensorReporteStrategy":
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    def clasificar(self, nivel: int | None) -> str:
        n = 0 if nivel is None else nivel
        if UmbralesReporte.INSTANCIA.es_optimo(n):
            return "OK"
        if UmbralesReporte.INSTANCIA.es_advertencia(n):
            return "ADVERTENCIA"
        return "FALLA"


class EstadoSensorFiltroStrategy(EstadoSensorStrategy):
    """Etiquetas de auditoría/filtros: "optimo", "advertencia", "falla"."""

    _instancia = None

    @classmethod
    def get_instancia(cls) -> "EstadoSensorFiltroStrategy":
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    def clasificar(self, nivel: int | None) -> str:
        n = 0 if nivel is None else nivel
        if UmbralesReporte.INSTANCIA.es_optimo(n):
            return "optimo"
        if UmbralesReporte.INSTANCIA.es_advertencia(n):
            return "advertencia"
        return "falla"


class ClasificadorEstadoSensor:
    """Contexto del patrón: mantiene una estrategia y delega en ella; se puede cambiar en ejecución."""

    def __init__(self, strategy: EstadoSensorStrategy | None):
        self._strategy = strategy

    def set_strategy(self, strategy: EstadoSensorStrategy) -> None:
        self._strategy = strategy

    def get_strategy(self) -> EstadoSensorStrategy | None:
        return self._strategy

    def clasificar(self, nivel: int | None) -> str:
        if self._strategy is None:
            raise RuntimeError("No se ha configurado una estrategia de clasificación.")
        return self._strategy.clasificar(nivel)
