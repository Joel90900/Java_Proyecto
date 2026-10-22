package com.example.sensores_vsc.patrones.comportamiento.estrategia;

/**
 * GoF – Strategy.
 * Contrato de las estrategias de clasificación de estado de un sensor.
 */
@FunctionalInterface
public interface EstadoSensorStrategy {

    /**
     * Clasifica el nivel (porcentaje de desgaste/lectura) en un estado legible.
     *
     * @param nivel nivel del sensor, puede ser {@code null}
     * @return etiqueta de estado
     */
    String clasificar(Integer nivel);
}