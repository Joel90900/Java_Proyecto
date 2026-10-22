package com.example.sensores_vsc.patrones.comportamiento.estrategia;

import com.example.sensores_vsc.patrones.creacional.singleton.UmbralesReporte;

/**
 * GoF – Strategy.
 * Estrategia con etiquetas cortas (para PDF/reportes):
 * "OK", "ADVERTENCIA", "FALLA".
 */
public final class EstadoSensorReporteStrategy implements EstadoSensorStrategy {

    private static final EstadoSensorReporteStrategy INSTANCIA = new EstadoSensorReporteStrategy();

    private EstadoSensorReporteStrategy() {
    }

    public static EstadoSensorReporteStrategy getInstancia() {
        return INSTANCIA;
    }

    @Override
    public String clasificar(Integer nivel) {
        int n = nivel == null ? 0 : nivel;
        if (UmbralesReporte.INSTANCIA.esOptimo(n)) return "OK";
        if (UmbralesReporte.INSTANCIA.esAdvertencia(n)) return "ADVERTENCIA";
        return "FALLA";
    }
}