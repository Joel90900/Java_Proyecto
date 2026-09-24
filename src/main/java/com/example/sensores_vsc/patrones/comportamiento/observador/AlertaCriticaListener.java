package com.example.sensores_vsc.patrones.comportamiento.observador;

import com.example.sensores_vsc.model.Alerta;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/**
 * GoF – Observer (Listener).
 * Observa los eventos {@link AlertaCriticaEvento} y reacciona ante ellos.
 * Con Spring, el "observador" se suscribe automáticamente mediante {@link EventListener}.
 */
@Component
public class AlertaCriticaListener {

    private static final Logger LOG = LoggerFactory.getLogger(AlertaCriticaListener.class);

    @EventListener
    public void atenderAlertaCritica(AlertaCriticaEvento evento) {
        Alerta a = evento.getAlerta();
        LOG.warn("[OBSERVER] Alerta registrada -> Sensor '{}' (vehículo {}) nivel {}% | {}",
                a.getNombreSensor(), a.getIdVehiculo(), a.getNivel(), a.getMensaje());
    }
}