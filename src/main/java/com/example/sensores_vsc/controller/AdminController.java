package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.repository.ClienteRepository;
import com.example.sensores_vsc.repository.SensorRepository;
import com.example.sensores_vsc.repository.UsuarioRepository;
import com.example.sensores_vsc.repository.VehiculoRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;

/**
 * Controlador administrativo de AutoSen.
 * Administra el panel principal, usuarios, clientes y acciones operativas.
 * Cumple con el principio de responsabilidad única delegando la generación
 * y filtrado multicriterio de reportes a {@link ReporteController}.
 */
@Controller
@RequestMapping("/admin")
public class AdminController {

    @Autowired
    private ClienteRepository clienteRepository;

    @Autowired
    private VehiculoRepository vehiculoRepository;

    @Autowired
    private SensorRepository sensorRepository;

    @Autowired
    private UsuarioRepository usuarioRepository;

    @GetMapping
    public String index(Model model) {
        model.addAttribute("clientes", clienteRepository.findAll());
        model.addAttribute("usuarios", usuarioRepository.findAll());
        return "admin/dashboard";
    }

    @GetMapping("/login")
    public String loginPage() {
        return "admin/login";
    }

    @GetMapping("/nosotros")
    public String nosotrosPage() {
        return "cliente/nosotros";
    }

    @PostMapping("/cliente/{id}/estado")
    public String cambiarEstado(@PathVariable Long id) {
        Cliente c = clienteRepository.findById(id).orElseThrow();
        c.setEstado("activo".equals(c.getEstado()) ? "bloqueado" : "activo");
        clienteRepository.save(c);
        return "redirect:/admin";
    }

    @PostMapping("/vehiculo/{id}/eliminar")
    public String eliminarVehiculo(@PathVariable Long id) {
        sensorRepository.deleteByVehiculoIdVehiculo(id);
        vehiculoRepository.deleteById(id);
        return "redirect:/admin";
    }

    @PostMapping("/sensor/{id}/eliminar")
    public String eliminarSensor(@PathVariable Long id) {
        sensorRepository.deleteById(id);
        return "redirect:/admin";
    }
}