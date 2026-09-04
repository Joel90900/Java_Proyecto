package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Vehiculo;
import com.example.sensores_vsc.model.Sensor;
import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.repository.VehiculoRepository;
import com.example.sensores_vsc.repository.SensorRepository;
import com.example.sensores_vsc.repository.ClienteRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.time.LocalDateTime;
import java.util.List;

@Controller
public class ReporteController {

    @Autowired
    private VehiculoRepository vehiculoRepository;

    @Autowired
    private SensorRepository sensorRepository;

    @Autowired
    private ClienteRepository clienteRepository;

    // ---------------------------------------------------------
    // REPORTE GENERAL (admin/reportes-pdf.html)
    // ---------------------------------------------------------
    @GetMapping("/admin/reportes-pdf")
    public String reporteGeneral(Model model) {

        List<Vehiculo> vehiculos = vehiculoRepository.findAll();

        long sensoresOptimos = 0, sensoresAdvertencia = 0, sensoresFalla = 0;

        for (Vehiculo v : vehiculos) {
List<Sensor> sensores = sensorRepository.findByVehiculoIdVehiculo(v.getIdVehiculo());
            for (Sensor s : sensores) {
                switch (s.getEstado()) {
                    case "optimo" -> sensoresOptimos++;
                    case "advertencia" -> sensoresAdvertencia++;
                    case "falla" -> sensoresFalla++;
                }
            }
        }

        List<Sensor> alertas = sensorRepository.findByEstadoIn(
                List.of("advertencia", "falla"));

        model.addAttribute("vehiculos", vehiculos);
        model.addAttribute("alertas", alertas);
        model.addAttribute("totalVehiculos", vehiculos.size());
        model.addAttribute("sensoresOptimos", sensoresOptimos);
        model.addAttribute("sensoresAdvertencia", sensoresAdvertencia);
        model.addAttribute("sensoresFalla", sensoresFalla);
        model.addAttribute("fechaGeneracion", LocalDateTime.now());
        model.addAttribute("adminNombre", "Administrador");
        model.addAttribute("reporteId", "RPT-" + System.currentTimeMillis());

        return "admin/reportes-pdf";
    }

    // ---------------------------------------------------------
    // REPORTE POR CLIENTE (admin/reporte-cliente-pdf.html)
    // ---------------------------------------------------------
    @GetMapping("/admin/reporte-cliente-pdf/{clienteId}")
    public String reporteCliente(@PathVariable Long clienteId, Model model) {

        Cliente cliente = clienteRepository.findById(clienteId)
                .orElseThrow(() -> new RuntimeException("Cliente no encontrado"));

        List<Vehiculo> vehiculos = vehiculoRepository.findByClienteIdCliente(clienteId);
        for (Vehiculo v : vehiculos) {
List<Sensor> sensores = sensorRepository.findByVehiculoIdVehiculo(v.getIdVehiculo());
            v.setSensores(sensores);
        }

        model.addAttribute("cliente", cliente);
        model.addAttribute("vehiculos", vehiculos);
        model.addAttribute("fechaGeneracion", LocalDateTime.now());
        model.addAttribute("adminNombre", "Administrador");
        model.addAttribute("reporteId", "RPT-" + System.currentTimeMillis());

        return "admin/reporte-cliente-pdf";
    }
}