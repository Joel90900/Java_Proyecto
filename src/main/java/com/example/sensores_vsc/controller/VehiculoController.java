package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.*;
import com.example.sensores_vsc.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
public class VehiculoController {

    @Autowired
    private VehiculoRepository vehiculoRepository;

    @Autowired
    private SensorRepository sensorRepository;

    @Autowired
    private ClienteRepository clienteRepository;

    @GetMapping("/vehiculos/crear")
    public String showCrear() {
        return "paginas/crear-vehiculo";
    }

    @PostMapping("/vehiculos/crear")
    public String crear(@RequestParam String nombreVehiculo,
                        @RequestParam String marca,
                        @RequestParam String modelo,
                        @RequestParam String color,
                        @RequestParam String placa,
                        @RequestParam String tipoPlaca,
                        @AuthenticationPrincipal UserDetails userDetails,
                        Model model) {

        if (nombreVehiculo.isBlank() || marca.isBlank() || modelo.isBlank() ||
            color.isBlank() || placa.isBlank() || tipoPlaca.isBlank()) {
            model.addAttribute("error", "Todos los campos son obligatorios.");
            return "paginas/crear-vehiculo";
        }

        try {
            int anio = Integer.parseInt(modelo);
            if (anio < 1990 || anio > 2030) {
                model.addAttribute("error", "El año debe estar entre 1990 y 2030.");
                return "paginas/crear-vehiculo";
            }
        } catch (NumberFormatException e) {
            model.addAttribute("error", "El año debe ser un número válido.");
            return "paginas/crear-vehiculo";
        }

        if (vehiculoRepository.findByPlaca(placa.toUpperCase()).isPresent()) {
            model.addAttribute("error", "Ya existe un vehículo registrado con esa placa.");
            return "paginas/crear-vehiculo";
        }

        if (!placa.toUpperCase().matches("^[A-Z]{3}[-]?[0-9]{3}$")) {
            model.addAttribute("error", "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.");
            return "paginas/crear-vehiculo";
        }

        Cliente cliente = clienteRepository.findByCorreo(userDetails.getUsername()).orElseThrow();

        Vehiculo v = new Vehiculo();
        v.setNombreVehiculo(nombreVehiculo.trim());
        v.setMarca(marca.trim());
        v.setModelo(modelo + "-01-01");
        v.setColor(color.trim());
        v.setPlaca(placa.toUpperCase().trim());
        v.setTipoPlaca(tipoPlaca);
        v.setCliente(cliente);
        vehiculoRepository.save(v);

        String[][] sensoresDefecto = {
            {"Sensor de Flujo de Masa de Aire (MAF)", "MAF", "Falla en flujo de aire"},
            {"Sensor de Oxígeno (O2)", "O2", "Falla en mezcla"},
            {"Sensor de Temperatura del Refrigerante (ECT)", "ECT", "Sobrecalentamiento"},
            {"Sensor de Presión Absoluta del Colector (MAP)", "MAP", "Falla en presión"}
        };

        for (String[] s : sensoresDefecto) {
            Sensor sensor = new Sensor();
            sensor.setNombreSensor(s[0]);
            sensor.setTipoSensor(s[1]);
            sensor.setTipoDano(s[2]);
            sensor.setNivel(0);
            sensor.setVehiculo(v);
            sensorRepository.save(sensor);
        }

        return "redirect:/vehiculos";
    }

    @GetMapping("/vehiculos/{id}/editar")
    public String showEditar(@PathVariable Long id,
                             @AuthenticationPrincipal UserDetails userDetails,
                             Model model) {
        Cliente cliente = clienteRepository.findByCorreo(userDetails.getUsername()).orElseThrow();
        Vehiculo v = vehiculoRepository.findById(id).orElseThrow();

        if (!v.getCliente().getIdCliente().equals(cliente.getIdCliente())) {
            return "redirect:/vehiculos";
        }

        model.addAttribute("vehiculo", v);
        model.addAttribute("cliente", cliente);
        return "paginas/editar-vehiculo";
    }

    @PostMapping("/vehiculos/{id}/editar")
    public String editar(@PathVariable Long id,
                         @RequestParam String nombreVehiculo,
                         @RequestParam String marca,
                         @RequestParam String color,
                         @RequestParam String placa,
                         @RequestParam String tipoPlaca,
                         @AuthenticationPrincipal UserDetails userDetails,
                         Model model) {

        Cliente cliente = clienteRepository.findByCorreo(userDetails.getUsername()).orElseThrow();
        Vehiculo v = vehiculoRepository.findById(id).orElseThrow();

        if (!v.getCliente().getIdCliente().equals(cliente.getIdCliente())) {
            return "redirect:/vehiculos";
        }

        if (nombreVehiculo.isBlank() || marca.isBlank() || color.isBlank() || placa.isBlank()) {
            model.addAttribute("error", "Todos los campos son obligatorios.");
            model.addAttribute("vehiculo", v);
            model.addAttribute("cliente", cliente);
            return "paginas/editar-vehiculo";
        }

        if (!placa.toUpperCase().equals(v.getPlaca()) &&
            vehiculoRepository.findByPlaca(placa.toUpperCase()).isPresent()) {
            model.addAttribute("error", "Ya existe un vehículo con esa placa.");
            model.addAttribute("vehiculo", v);
            model.addAttribute("cliente", cliente);
            return "paginas/editar-vehiculo";
        }

        v.setNombreVehiculo(nombreVehiculo.trim());
        v.setMarca(marca.trim());
        v.setColor(color.trim());
        v.setPlaca(placa.toUpperCase().trim());
        v.setTipoPlaca(tipoPlaca);
        vehiculoRepository.save(v);

        return "redirect:/vehiculos";
    }

    @PostMapping("/vehiculos/{id}/eliminar")
    public String eliminar(@PathVariable Long id,
                           @AuthenticationPrincipal UserDetails userDetails) {
        Cliente cliente = clienteRepository.findByCorreo(userDetails.getUsername()).orElseThrow();
        Vehiculo v = vehiculoRepository.findById(id).orElseThrow();

        if (v.getCliente().getIdCliente().equals(cliente.getIdCliente())) {
            sensorRepository.deleteByVehiculoIdVehiculo(id);
            vehiculoRepository.deleteById(id);
        }

        return "redirect:/vehiculos";
    }
}