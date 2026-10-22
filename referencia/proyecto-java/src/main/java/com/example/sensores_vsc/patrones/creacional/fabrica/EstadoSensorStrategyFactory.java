package com.example.sensores_vsc.patrones.creacional.fabrica;

import com.example.sensores_vsc.patrones.comportamiento.estrategia.EstadoSensorFiltroStrategy;
import com.example.sensores_vsc.patrones.comportamiento.estrategia.EstadoSensorReporteStrategy;
import com.example.sensores_vsc.patrones.comportamiento.estrategia.EstadoSensorStrategy;

/**
 * GoF – Simple Factory / Factory Method.
 * Encapsula la creación de las estrategias de clasificación de estado.
 * El cliente solo indica el tipo deseado y la fábrica decide qué
 * estrategia concreta instanciar (o reutilizar).
 */
public final class EstadoSensorStrategyFactory {

    private EstadoSensorStrategyFactory() {
    }

    public static EstadoSensorStrategy crear(TipoEstado tipo) {
        return switch (tipo) {
            case REPORTE -> EstadoSensorReporteStrategy.getInstancia();
            case FILTRO -> EstadoSensorFiltroStrategy.getInstancia();
        };
    }
}