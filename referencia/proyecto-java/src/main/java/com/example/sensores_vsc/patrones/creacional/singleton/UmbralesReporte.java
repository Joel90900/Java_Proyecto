package com.example.sensores_vsc.patrones.creacional.singleton;

/**
 * GoF – Singleton (mediante enum, "Effective Java").
 * Centraliza los umbrales de nivel de los sensores para toda la aplicación.
 * Solo existe una instancia: {@code UmbralesReporte.INSTANCIA}.
 */
public enum UmbralesReporte {

    INSTANCIA;

    public static final int MINIMO_ADVERTENCIA = 40;
    public static final int MINIMO_FALLA = 70;

    public boolean esOptimo(int nivel) {
        return nivel < MINIMO_ADVERTENCIA;
    }

    public boolean esAdvertencia(int nivel) {
        return nivel >= MINIMO_ADVERTENCIA && nivel < MINIMO_FALLA;
    }

    public boolean esFalla(int nivel) {
        return nivel >= MINIMO_FALLA;
    }
}