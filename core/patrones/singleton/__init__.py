"""
GoF – Singleton (mediante Enum, "Effective Java").

Centraliza los umbrales de nivel de los sensores para toda la aplicación.
Solo existe una instancia: UmbralesReporte.INSTANCIA.
"""
import enum


class UmbralesReporte(enum.Enum):
    INSTANCIA = "INSTANCIA"

    # nonmember: son constantes de la clase, no instancias adicionales del Enum.
    MINIMO_ADVERTENCIA = enum.nonmember(40)
    MINIMO_FALLA = enum.nonmember(70)

    def es_optimo(self, nivel: int) -> bool:
        return nivel < self.MINIMO_ADVERTENCIA

    def es_advertencia(self, nivel: int) -> bool:
        return self.MINIMO_ADVERTENCIA <= nivel < self.MINIMO_FALLA

    def es_falla(self, nivel: int) -> bool:
        return nivel >= self.MINIMO_FALLA
