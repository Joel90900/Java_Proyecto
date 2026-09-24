package com.example.sensores_vsc.patrones.creacional.fabrica;

/**
 * Tipos de estrategia que la fábrica puede crear.
 */
public enum TipoEstado {
    /** Etiquetas cortas para PDF/reportes: OK, ADVERTENCIA, FALLA */
    REPORTE,
    /** Etiquetas de auditoría/filtros: optimo, advertencia, falla */
    FILTRO
}