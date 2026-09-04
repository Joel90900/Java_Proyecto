package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.model.Sensor;
import com.example.sensores_vsc.model.Vehiculo;
import com.example.sensores_vsc.repository.ClienteRepository;
import com.example.sensores_vsc.repository.SensorRepository;
import com.example.sensores_vsc.repository.VehiculoRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
public class DashboardController {

    @Autowired
    private ClienteRepository clienteRepository;

    @Autowired
    private VehiculoRepository vehiculoRepository;

    @Autowired
    private SensorRepository sensorRepository;

    @GetMapping("/dashboard")
    public String dashboard(@AuthenticationPrincipal UserDetails userDetails, Model model) {
        Cliente cliente = clienteRepository.findByCorreo(userDetails.getUsername()).orElseThrow();
        List<Vehiculo> vehiculos = vehiculoRepository.findByClienteIdCliente(cliente.getIdCliente());

        List<Long> vehiculoIds = vehiculos.stream().map(Vehiculo::getIdVehiculo).toList();

        List<Sensor> sensores = vehiculoIds.isEmpty() ? List.of() :
            sensorRepository.findAll().stream()
                .filter(s -> s.getVehiculo() != null &&
                    vehiculoIds.contains(s.getVehiculo().getIdVehiculo()))
                .toList();

        long sensoresOk   = sensores.stream().filter(s -> s.getNivel() < 40).count();
        long advertencias = sensores.stream().filter(s -> s.getNivel() >= 40 && s.getNivel() < 70).count();
        long fallas       = sensores.stream().filter(s -> s.getNivel() >= 70).count();

        model.addAttribute("cliente", cliente);
        model.addAttribute("vehiculos", vehiculos);
        model.addAttribute("totalSensores", sensores.size());
        model.addAttribute("sensoresOk", sensoresOk);
        model.addAttribute("advertencias", advertencias);
        model.addAttribute("fallas", fallas);

        return "paginas/dashboard";
    }

  @GetMapping("/vehiculos")
public String misVehiculos(@AuthenticationPrincipal UserDetails userDetails, Model model) {
    Cliente cliente = clienteRepository.findByCorreo(userDetails.getUsername()).orElseThrow();
    List<Vehiculo> vehiculos = vehiculoRepository.findByClienteIdCliente(cliente.getIdCliente());
    model.addAttribute("cliente", cliente);
    model.addAttribute("vehiculos", vehiculos);
    return "paginas/mis-vehiculos";

}

@GetMapping("/sensores")
public String sensores(@AuthenticationPrincipal UserDetails userDetails, Model model) {
    Cliente cliente = clienteRepository.findByCorreo(userDetails.getUsername()).orElseThrow();
    List<Vehiculo> vehiculos = vehiculoRepository.findByClienteIdCliente(cliente.getIdCliente());
    model.addAttribute("vehiculos", vehiculos);
    model.addAttribute("cliente", cliente);
    return "paginas/sensores";
}
}