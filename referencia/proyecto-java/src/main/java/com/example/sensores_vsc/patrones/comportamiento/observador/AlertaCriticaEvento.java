package com.example.sensores_vsc.patrones.comportamiento.observador;

import com.example.sensores_vsc.model.Alerta;
import org.springframework.context.ApplicationEvent;

/**
 * GoF – Observer (Evento).
 * Se publica cuando un sensor alcanza un nivel crítico y se registra una alerta.
 */
public class AlertaCriticaEvento extends ApplicationEvent {

    private final Alerta alerta;

    public AlertaCriticaEvento(Object source, Alerta alerta) {
        super(source);
        this.alerta = alerta;
    }

    public Alerta getAlerta() {
        return alerta;
    }
}