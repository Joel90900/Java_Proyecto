package com.example.sensores_vsc.model;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "vehiculo")
public class Vehiculo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "Id_vehiculo")
    private Long idVehiculo;

    @Column(name = "Nombre_vehiculo")
    private String nombreVehiculo;

    @Column(name = "Marca")
    private String marca;

    @Column(name = "Modelo")
    private String modelo;

    @Column(name = "Color")
    private String color;

    @Column(name = "Placa")
    private String placa;

    @Column(name = "Tipo_placa")
    private String tipoPlaca;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "Id_cliente")
    private Cliente cliente;

    @OneToMany(mappedBy = "vehiculo", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Sensor> sensores;

    public Long getIdVehiculo() { return idVehiculo; }
    public void setIdVehiculo(Long idVehiculo) { this.idVehiculo = idVehiculo; }
    public String getNombreVehiculo() { return nombreVehiculo; }
    public void setNombreVehiculo(String nombreVehiculo) { this.nombreVehiculo = nombreVehiculo; }
    public String getMarca() { return marca; }
    public void setMarca(String marca) { this.marca = marca; }
    public String getModelo() { return modelo; }
    public void setModelo(String modelo) { this.modelo = modelo; }
    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }
    public String getPlaca() { return placa; }
    public void setPlaca(String placa) { this.placa = placa; }
    public String getTipoPlaca() { return tipoPlaca; }
    public void setTipoPlaca(String tipoPlaca) { this.tipoPlaca = tipoPlaca; }
    public Cliente getCliente() { return cliente; }
    public void setCliente(Cliente cliente) { this.cliente = cliente; }
    public List<Sensor> getSensores() { return sensores; }
    public void setSensores(List<Sensor> sensores) { this.sensores = sensores; }
}