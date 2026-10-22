from django.test import SimpleTestCase

from core.models import Alerta
from core.patrones.estrategia import ClasificadorEstadoSensor, EstadoSensorFiltroStrategy, EstadoSensorReporteStrategy
from core.patrones.fabrica import EstadoSensorStrategyFactory, TipoEstado
from core.patrones.observador import alerta_critica
from core.patrones.singleton import UmbralesReporte

NIVELES = (None, 0, 39, 40, 69, 70, 100)


class PatronesTests(SimpleTestCase):
    def test_estrategia_reporte(self):
        s = EstadoSensorReporteStrategy.get_instancia()
        self.assertEqual([s.clasificar(n) for n in NIVELES],
                         ["OK", "OK", "OK", "ADVERTENCIA", "ADVERTENCIA", "FALLA", "FALLA"])

    def test_estrategia_filtro(self):
        s = EstadoSensorFiltroStrategy.get_instancia()
        self.assertEqual([s.clasificar(n) for n in NIVELES],
                         ["optimo", "optimo", "optimo", "advertencia", "advertencia", "falla", "falla"])

    def test_fabrica_devuelve_instancias_unicas(self):
        self.assertIs(EstadoSensorStrategyFactory.crear(TipoEstado.REPORTE), EstadoSensorReporteStrategy.get_instancia())
        self.assertIs(EstadoSensorStrategyFactory.crear(TipoEstado.FILTRO), EstadoSensorFiltroStrategy.get_instancia())

    def test_contexto_cambia_de_estrategia(self):
        c = ClasificadorEstadoSensor(EstadoSensorStrategyFactory.crear(TipoEstado.REPORTE))
        self.assertEqual(c.clasificar(50), "ADVERTENCIA")
        c.set_strategy(EstadoSensorStrategyFactory.crear(TipoEstado.FILTRO))
        self.assertEqual(c.clasificar(50), "advertencia")
        with self.assertRaises(RuntimeError):
            ClasificadorEstadoSensor(None).clasificar(10)

    def test_singleton(self):
        self.assertEqual(len(UmbralesReporte), 1)
        self.assertEqual((UmbralesReporte.MINIMO_ADVERTENCIA, UmbralesReporte.MINIMO_FALLA), (40, 70))
        u = UmbralesReporte.INSTANCIA
        self.assertEqual([u.es_optimo(39), u.es_optimo(40), u.es_advertencia(69), u.es_advertencia(70), u.es_falla(70)],
                         [True, False, True, False, True])

    def test_observador_registra_la_alerta(self):
        alerta = Alerta(id_vehiculo=4, nombre_sensor="RPM del motor", nivel=73,
                        mensaje="Falla crítica en RPM del motor: nivel 73% (2345.0 rpm).")
        with self.assertLogs("autosen.observador", level="WARNING") as registro:
            alerta_critica.send(sender=None, alerta=alerta)
        self.assertEqual(registro.output, [
            "WARNING:autosen.observador:[OBSERVER] Alerta registrada -> Sensor 'RPM del motor' "
            "(vehículo 4) nivel 73% | Falla crítica en RPM del motor: nivel 73% (2345.0 rpm)."])
