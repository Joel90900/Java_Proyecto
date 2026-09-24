package com.example.sensores_vsc.patrones.comportamiento.estrategia;

import com.example.sensores_vsc.patrones.creacional.singleton.UmbralesReporte;

/**
 * GoF – Strategy.
 * Estrategia con etiquetas de auditoría/filtros:
 * "optimo", "advertencia", "falla".
 */
public final class EstadoSensorFiltroStrategy implements EstadoSensorStrategy {

    private static final EstadoSensorFiltroStrategy INSTANCIA = new EstadoSensorFiltroStrategy();

    private EstadoSensorFiltroStrategy() {
    }

    public static EstadoSensorFiltroStrategy getInstancia() {
        return INSTANCIA;
    }

    @Override
    public String clasificar(Integer nivel) {
        int n = nivel == null ? 0 : nivel;
        if (UmbralesReporte.INSTANCIA.esOptimo(n)) return "optimo";
        if (UmbralesReporte.INSTANCIA.esAdvertencia(n)) return "advertencia";
        return "falla";
    }
}