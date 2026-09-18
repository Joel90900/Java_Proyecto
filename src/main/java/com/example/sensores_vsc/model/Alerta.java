package com.example.sensores_vsc.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "alertas")
public class Alerta {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "Id_alerta")
    private Long idAlerta;

    @Column(name = "Id_vehiculo")
    private Long idVehiculo;

    @Column(name = "Nombre_sensor")
    private String nombreSensor;

    @Column(name = "Tipo_sensor")
    private String tipoSensor;

    @Column(name = "Valor")
    private Double valor;

    @Column(name = "Nivel")
    private Integer nivel;

    @Column(name = "Tipo")
    private String tipo;

    @Column(name = "Mensaje")
    private String mensaje;

    @Column(name = "Leida")
    private Integer leida;

    @Column(name = "Fecha_alerta")
    private LocalDateTime fechaAlerta;

    public Long getIdAlerta() { return idAlerta; }
    public void setIdAlerta(Long idAlerta) { this.idAlerta = idAlerta; }
    public Long getIdVehiculo() { return idVehiculo; }
    public void setIdVehiculo(Long idVehiculo) { this.idVehiculo = idVehiculo; }
    public String getNombreSensor() { return nombreSensor; }
    public void setNombreSensor(String nombreSensor) { this.nombreSensor = nombreSensor; }
    public String getTipoSensor() { return tipoSensor; }
    public void setTipoSensor(String tipoSensor) { this.tipoSensor = tipoSensor; }
    public Double getValor() { return valor; }
    public void setValor(Double valor) { this.valor = valor; }
    public Integer getNivel() { return nivel; }
    public void setNivel(Integer nivel) { this.nivel = nivel; }
    public String getTipo() { return tipo; }
    public void setTipo(String tipo) { this.tipo = tipo; }
    public String getMensaje() { return mensaje; }
    public void setMensaje(String mensaje) { this.mensaje = mensaje; }
    public Integer getLeida() { return leida; }
    public void setLeida(Integer leida) { this.leida = leida; }
    public LocalDateTime getFechaAlerta() { return fechaAlerta; }
    public void setFechaAlerta(LocalDateTime fechaAlerta) { this.fechaAlerta = fechaAlerta; }
}