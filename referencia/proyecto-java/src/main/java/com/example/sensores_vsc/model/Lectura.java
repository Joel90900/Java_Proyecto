package com.example.sensores_vsc.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "lecturas")
public class Lectura {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "Id_lectura")
    private Long idLectura;

    @Column(name = "Id_vehiculo")
    private Long idVehiculo;

    @Column(name = "Nombre_sensor")
    private String nombreSensor;

    @Column(name = "Tipo_sensor")
    private String tipoSensor;

    @Column(name = "Valor")
    private Double valor;

    @Column(name = "Unidad")
    private String unidad;

    @Column(name = "Nivel")
    private Integer nivel;

    @Column(name = "Estado")
    private String estado;

    @Column(name = "Fecha_lectura")
    private LocalDateTime fechaLectura;

    public Long getIdLectura() { return idLectura; }
    public void setIdLectura(Long idLectura) { this.idLectura = idLectura; }
    public Long getIdVehiculo() { return idVehiculo; }
    public void setIdVehiculo(Long idVehiculo) { this.idVehiculo = idVehiculo; }
    public String getNombreSensor() { return nombreSensor; }
    public void setNombreSensor(String nombreSensor) { this.nombreSensor = nombreSensor; }
    public String getTipoSensor() { return tipoSensor; }
    public void setTipoSensor(String tipoSensor) { this.tipoSensor = tipoSensor; }
    public Double getValor() { return valor; }
    public void setValor(Double valor) { this.valor = valor; }
    public String getUnidad() { return unidad; }
    public void setUnidad(String unidad) { this.unidad = unidad; }
    public Integer getNivel() { return nivel; }
    public void setNivel(Integer nivel) { this.nivel = nivel; }
    public String getEstado() { return estado; }
    public void setEstado(String estado) { this.estado = estado; }
    public LocalDateTime getFechaLectura() { return fechaLectura; }
    public void setFechaLectura(LocalDateTime fechaLectura) { this.fechaLectura = fechaLectura; }
}