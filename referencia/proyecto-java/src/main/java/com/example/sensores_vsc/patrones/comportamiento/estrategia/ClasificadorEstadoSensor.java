package com.example.sensores_vsc.patrones.comportamiento.estrategia;

/**
 * GoF – Strategy (Contexto).
 * Mantiene una referencia a una estrategia de clasificación y delega en ella.
 * Permite cambiar de estrategia en tiempo de ejecución (polimorfismo).
 */
public final class ClasificadorEstadoSensor {

    private EstadoSensorStrategy strategy;

    public ClasificadorEstadoSensor(EstadoSensorStrategy strategy) {
        this.strategy = strategy;
    }

    public void setStrategy(EstadoSensorStrategy strategy) {
        this.strategy = strategy;
    }

    public EstadoSensorStrategy getStrategy() {
        return strategy;
    }

    public String clasificar(Integer nivel) {
        if (strategy == null) {
            throw new IllegalStateException("No se ha configurado una estrategia de clasificación.");
        }
        return strategy.clasificar(nivel);
    }
}