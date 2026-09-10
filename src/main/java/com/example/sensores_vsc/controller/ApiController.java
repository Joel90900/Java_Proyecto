package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.model.Sensor;
import com.example.sensores_vsc.model.Vehiculo;
import com.example.sensores_vsc.repository.ClienteRepository;
import com.example.sensores_vsc.repository.SensorRepository;
import com.example.sensores_vsc.repository.VehiculoRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

/**
 * API REST de AutoSen para la aplicación móvil Android.
 * Todos los endpoints devuelven JSON.
 */
@RestController
@RequestMapping("/api")
public class ApiController {

    @Autowired
    private ClienteRepository clienteRepository;

    @Autowired
    private VehiculoRepository vehiculoRepository;

    @Autowired
    private SensorRepository sensorRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private static final String[][] SENSORES_POR_DEFECTO = {
        {"Sensor de Flujo de Masa de Aire (MAF)", "MAF", "Falla en flujo de aire"},
        {"Sensor de Oxígeno (O2)", "O2", "Falla en mezcla"},
        {"Sensor de Temperatura del Refrigerante (ECT)", "ECT", "Sobrecalentamiento"},
        {"Sensor de Presión Absoluta del Colector (MAP)", "MAP", "Falla en presión"}
    };

    // ---------------------------------------------------------
    // AUTH
    // ---------------------------------------------------------

    @PostMapping("/auth/register")
    public Map<String, Object> registrar(@RequestParam String nombre,
                                         @RequestParam String apellido,
                                         @RequestParam String correo,
                                         @RequestParam String contrasena) {
        Map<String, Object> resp = new LinkedHashMap<>();
        if (clienteRepository.findByCorreo(correo).isPresent()) {
            resp.put("ok", false);
            resp.put("mensaje", "El correo ya está registrado.");
            return resp;
        }
        Cliente cliente = new Cliente();
        cliente.setNombreCliente(nombre.trim());
        cliente.setApellidoCliente(apellido.trim());
        cliente.setCorreo(correo.trim());
        cliente.setContrasena(passwordEncoder.encode(contrasena));
        cliente.setEstado("activo");
        clienteRepository.save(cliente);
        resp.put("ok", true);
        resp.put("mensaje", "Cuenta creada correctamente.");
        resp.put("cliente", clienteInfo(cliente));
        return resp;
    }

    @PostMapping("/auth/login")
    public Map<String, Object> login(@RequestParam String correo,
                                     @RequestParam String contrasena) {
        Map<String, Object> resp = new LinkedHashMap<>();
        Cliente cliente = clienteRepository.findByCorreo(correo).orElse(null);
        if (cliente == null || !passwordEncoder.matches(contrasena, cliente.getContrasena())) {
            resp.put("ok", false);
            resp.put("mensaje", "Correo o contraseña incorrectos.");
            return resp;
        }
        if ("bloqueado".equals(cliente.getEstado())) {
            resp.put("ok", false);
            resp.put("mensaje", "Tu cuenta está bloqueada. Contacta al administrador.");
            return resp;
        }
        resp.put("ok", true);
        resp.put("mensaje", "Bienvenido.");
        resp.put("cliente", clienteInfo(cliente));
        return resp;
    }

    // ---------------------------------------------------------
    // DATOS DEL CLIENTE (dashboard / vehículos / sensores)
    // ---------------------------------------------------------

    @GetMapping("/cliente/{correo}")
    public Map<String, Object> datosCliente(@PathVariable String correo) {
        Map<String, Object> resp = new LinkedHashMap<>();
        Cliente cliente = clienteRepository.findByCorreo(correo).orElse(null);
        if (cliente == null) {
            resp.put("ok", false);
            resp.put("mensaje", "Cliente no encontrado.");
            return resp;
        }
        List<Vehiculo> vehiculos = vehiculoRepository.findByClienteIdCliente(cliente.getIdCliente());
        List<Map<String, Object>> vehiculosJson = new ArrayList<>();
        long sensoresOk = 0, advertencias = 0, fallas = 0, totalSensores = 0;
        for (Vehiculo v : vehiculos) {
            List<Sensor> sensores = sensorRepository.findByVehiculoIdVehiculo(v.getIdVehiculo());
            List<Map<String, Object>> sensoresJson = new ArrayList<>();
            for (Sensor s : sensores) {
                Map<String, Object> sJson = sensorInfo(s);
                if (s.getNivel() < 40) sensoresOk++;
                else if (s.getNivel() < 70) advertencias++;
                else fallas++;
                totalSensores++;
                sensoresJson.add(sJson);
            }
            Map<String, Object> vJson = new LinkedHashMap<>();
            vJson.put("idVehiculo", v.getIdVehiculo());
            vJson.put("nombreVehiculo", v.getNombreVehiculo());
            vJson.put("marca", v.getMarca());
            vJson.put("modelo", anioVehiculo(v.getModelo()));
            vJson.put("color", v.getColor());
            vJson.put("placa", v.getPlaca());
            vJson.put("tipoPlaca", v.getTipoPlaca());
            vJson.put("sensores", sensoresJson);
            vehiculosJson.add(vJson);
        }
        resp.put("ok", true);
        resp.put("cliente", clienteInfo(cliente));
        resp.put("vehiculos", vehiculosJson);
        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("totalVehiculos", vehiculosJson.size());
        stats.put("totalSensores", totalSensores);
        stats.put("sensoresOk", sensoresOk);
        stats.put("advertencias", advertencias);
        stats.put("fallas", fallas);
        resp.put("estadisticas", stats);
        return resp;
    }

    // ---------------------------------------------------------
    // CREAR VEHÍCULO (genera los 4 sensores automáticos)
    // ---------------------------------------------------------

    @PostMapping("/vehiculos/crear")
    public Map<String, Object> crearVehiculo(@RequestParam String correo,
                                             @RequestParam String nombreVehiculo,
                                             @RequestParam String marca,
                                             @RequestParam String modelo,
                                             @RequestParam String color,
                                             @RequestParam String placa,
                                             @RequestParam String tipoPlaca) {
        Map<String, Object> resp = new LinkedHashMap<>();
        Cliente cliente = clienteRepository.findByCorreo(correo).orElse(null);
        if (cliente == null) {
            resp.put("ok", false);
            resp.put("mensaje", "Cliente no encontrado.");
            return resp;
        }
        if (nombreVehiculo.isBlank() || marca.isBlank() || modelo.isBlank() ||
            color.isBlank() || placa.isBlank() || tipoPlaca.isBlank()) {
            resp.put("ok", false);
            resp.put("mensaje", "Todos los campos son obligatorios.");
            return resp;
        }
        try {
            int anio = Integer.parseInt(modelo.trim());
            if (anio < 1990 || anio > 2030) {
                resp.put("ok", false);
                resp.put("mensaje", "El año debe estar entre 1990 y 2030.");
                return resp;
            }
        } catch (NumberFormatException e) {
            resp.put("ok", false);
            resp.put("mensaje", "El año debe ser un número válido.");
            return resp;
        }
        String placaNormalizada = placa.toUpperCase().trim();
        if (vehiculoRepository.findByPlaca(placaNormalizada).isPresent()) {
            resp.put("ok", false);
            resp.put("mensaje", "Ya existe un vehículo registrado con esa placa.");
            return resp;
        }
        if (!placaNormalizada.matches("^[A-Z]{3}[-]?[0-9]{3}$")) {
            resp.put("ok", false);
            resp.put("mensaje", "Formato de placa inválido. Ejemplo: ABC123 o ABC-123.");
            return resp;
        }

        Vehiculo v = new Vehiculo();
        v.setNombreVehiculo(nombreVehiculo.trim());
        v.setMarca(marca.trim());
        v.setModelo(modelo.trim() + "-01-01");
        v.setColor(color.trim());
        v.setPlaca(placaNormalizada);
        v.setTipoPlaca(tipoPlaca);
        v.setCliente(cliente);
        vehiculoRepository.save(v);

        for (String[] s : SENSORES_POR_DEFECTO) {
            Sensor sensor = new Sensor();
            sensor.setNombreSensor(s[0]);
            sensor.setTipoSensor(s[1]);
            sensor.setTipoDano(s[2]);
            sensor.setNivel(0);
            sensor.setVehiculo(v);
            sensorRepository.save(sensor);
        }

        resp.put("ok", true);
        resp.put("mensaje", "Vehículo registrado correctamente.");
        return resp;
    }

    // ---------------------------------------------------------
    // SIMULACIÓN DE LECTURAS OBD2 (botón Bluetooth)
    // ---------------------------------------------------------

    @PostMapping("/bluetooth/simular")
    public Map<String, Object> simularLecturas(@RequestParam String correo) {
        Map<String, Object> resp = new LinkedHashMap<>();
        Cliente cliente = clienteRepository.findByCorreo(correo).orElse(null);
        if (cliente == null) {
            resp.put("ok", false);
            resp.put("mensaje", "Cliente no encontrado.");
            return resp;
        }
        List<Vehiculo> vehiculos = vehiculoRepository.findByClienteIdCliente(cliente.getIdCliente());
        for (Vehiculo v : vehiculos) {
            List<Sensor> sensores = sensorRepository.findByVehiculoIdVehiculo(v.getIdVehiculo());
            for (Sensor s : sensores) {
                int delta = ThreadLocalRandom.current().nextInt(-6, 26);
                int nuevoNivel = Math.max(0, Math.min(100, s.getNivel() + delta));
                s.setNivel(nuevoNivel);
                sensorRepository.save(s);
            }
        }
        return datosCliente(correo);
    }

    // ---------------------------------------------------------
    // HELPERS
    // ---------------------------------------------------------

    private Map<String, Object> clienteInfo(Cliente c) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("idCliente", c.getIdCliente());
        map.put("nombreCliente", c.getNombreCliente());
        map.put("apellidoCliente", c.getApellidoCliente());
        map.put("correo", c.getCorreo());
        map.put("estado", c.getEstado());
        return map;
    }

    private Map<String, Object> sensorInfo(Sensor s) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("idSensor", s.getIdSensor());
        map.put("nombreSensor", s.getNombreSensor());
        map.put("tipoSensor", s.getTipoSensor());
        map.put("tipoDano", s.getTipoDano());
        map.put("nivel", s.getNivel());
        return map;
    }

    private String anioVehiculo(String modelo) {
        if (modelo == null || modelo.isBlank()) return "";
        return modelo.split("-")[0];
    }
}