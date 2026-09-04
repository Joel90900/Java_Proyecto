package com.example.sensores_vsc.model;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "cliente")
public class Cliente {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "Id_cliente")
    private Long idCliente;

    @Column(name = "Nombre_cliente")
    private String nombreCliente;

    @Column(name = "Apellido_cliente")
    private String apellidoCliente;

    @Column(name = "Correo")
    private String correo;

    @Column(name = "Contrasena")
    private String contrasena;

    @Column(name = "Estado")
    private String estado;

    @OneToMany(mappedBy = "cliente", fetch = FetchType.LAZY)
    private List<Vehiculo> vehiculos;

    public Long getIdCliente() { return idCliente; }
    public void setIdCliente(Long idCliente) { this.idCliente = idCliente; }
    public String getNombreCliente() { return nombreCliente; }
    public void setNombreCliente(String nombreCliente) { this.nombreCliente = nombreCliente; }
    public String getApellidoCliente() { return apellidoCliente; }
    public void setApellidoCliente(String apellidoCliente) { this.apellidoCliente = apellidoCliente; }
    public String getCorreo() { return correo; }
    public void setCorreo(String correo) { this.correo = correo; }
    public String getContrasena() { return contrasena; }
    public void setContrasena(String contrasena) { this.contrasena = contrasena; }
    public String getEstado() { return estado; }
    public void setEstado(String estado) { this.estado = estado; }
    public List<Vehiculo> getVehiculos() { return vehiculos; }
    public void setVehiculos(List<Vehiculo> vehiculos) { this.vehiculos = vehiculos; }
}