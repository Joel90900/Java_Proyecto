package com.example.sensores_vsc.model;

import jakarta.persistence.*;

@Entity
@Table(name = "sensores")
public class Sensor {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "Id_sensor")
    private Long idSensor;

    @Column(name = "Nombre_sensor")
    private String nombreSensor;

    @Column(name = "Tipo_sensor")
    private String tipoSensor;

    @Column(name = "Tipo_daño")
    private String tipoDano;

    @Column(name = "Nivel")
    private Integer nivel;

    @Column(name = "Estado")
private String estado;

public String getEstado() { return estado; }
public void setEstado(String estado) { this.estado = estado; }

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "Id_vehiculo")
    private Vehiculo vehiculo;

    public Long getIdSensor() { return idSensor; }
    public void setIdSensor(Long idSensor) { this.idSensor = idSensor; }
    public String getNombreSensor() { return nombreSensor; }
    public void setNombreSensor(String nombreSensor) { this.nombreSensor = nombreSensor; }
    public String getTipoSensor() { return tipoSensor; }
    public void setTipoSensor(String tipoSensor) { this.tipoSensor = tipoSensor; }
    public String getTipoDano() { return tipoDano; }
    public void setTipoDano(String tipoDano) { this.tipoDano = tipoDano; }
    public Integer getNivel() { return nivel; }
    public void setNivel(Integer nivel) { this.nivel = nivel; }
    public Vehiculo getVehiculo() { return vehiculo; }
    public void setVehiculo(Vehiculo vehiculo) { this.vehiculo = vehiculo; }
}