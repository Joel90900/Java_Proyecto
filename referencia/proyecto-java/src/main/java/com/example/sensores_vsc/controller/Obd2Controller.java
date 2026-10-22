package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Alerta;
import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.model.Lectura;
import com.example.sensores_vsc.model.Sensor;
import com.example.sensores_vsc.model.Vehiculo;
import com.example.sensores_vsc.repository.AlertaRepository;
import com.example.sensores_vsc.repository.ClienteRepository;
import com.example.sensores_vsc.repository.LecturaRepository;
import com.example.sensores_vsc.repository.SensorRepository;
import com.example.sensores_vsc.repository.VehiculoRepository;
import com.example.sensores_vsc.patrones.comportamiento.observador.AlertaCriticaEvento;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;


@RestController
@RequestMapping("/api/obd2")
public class Obd2Controller {

    @Autowired
    private LecturaRepository lecturaRepository;

    @Autowired
    private AlertaRepository alertaRepository;

    @Autowired
    private VehiculoRepository vehiculoRepository;

    @Autowired
    private ClienteRepository clienteRepository;

    @Autowired
    private SensorRepository sensorRepository;

    @Autowired
    private ApplicationEventPublisher eventPublisher;

    
    @PostMapping("/lecturas")
    public Map<String, Object> guardarLectura(
            @RequestParam Long idVehiculo,
            @RequestParam String nombreSensor,
            @RequestParam String tipoSensor,
            @RequestParam Double valor,
            @RequestParam(required = false) String unidad) {

        Map<String, Object> resp = new LinkedHashMap<>();
        Vehiculo v = vehiculoRepository.findById(idVehiculo).orElse(null);
        if (v == null) {
            resp.put("ok", false);
            resp.put("mensaje", "Vehículo no encontrado.");
            return resp;
        }

        Lectura l = new Lectura();
        l.setIdVehiculo(idVehiculo);
        l.setNombreSensor(nombreSensor);
        l.setTipoSensor(tipoSensor);
        l.setValor(valor);
        l.setUnidad(unidad == null ? "" : unidad);
        l.setFechaLectura(LocalDateTime.now());

        // Calcular nivel porcentual y estado (misma lógica de la web)
        int nivel = calcularNivel(tipoSensor, valor);
        l.setNivel(nivel);
        l.setEstado(nivel < 40 ? "OK" : nivel < 70 ? "ADVERTENCIA" : "FALLA");
        lecturaRepository.save(l);

        if (nivel >= 40) {
            Alerta a = new Alerta();
            a.setIdVehiculo(idVehiculo);
            a.setNombreSensor(nombreSensor);
            a.setTipoSensor(tipoSensor);
            a.setValor(valor);
            a.setNivel(nivel);
            a.setTipo(nivel >= 70 ? "falla" : "advertencia");
            a.setMensaje(nivel >= 70
                    ? "Falla crítica en " + nombreSensor + ": nivel " + nivel + "% (" + valor + (unidad == null ? "" : " " + unidad) + ")."
                    : "Advertencia en " + nombreSensor + ": nivel " + nivel + "% (" + valor + (unidad == null ? "" : " " + unidad) + ").");
            a.setLeida(0);
            a.setFechaAlerta(LocalDateTime.now());
            alertaRepository.save(a);
            eventPublisher.publishEvent(new AlertaCriticaEvento(this, a));
        }

        resp.put("ok", true);
        resp.put("mensaje", "Lectura registrada.");
        resp.put("idLectura", l.getIdLectura());
        resp.put("nivel", nivel);
        resp.put("estado", l.getEstado());
        return resp;
    }

    @PostMapping("/vehiculo/{id}/elm")
    public Map<String, Object> guardarElm(@PathVariable Long id, @RequestParam String elmMac) {
        Map<String, Object> resp = new LinkedHashMap<>();
        Vehiculo v = vehiculoRepository.findById(id).orElse(null);
        if (v == null) {
            resp.put("ok", false);
            resp.put("mensaje", "Vehículo no encontrado.");
            return resp;
        }
        v.setElmMac(elmMac);
        vehiculoRepository.save(v);
        resp.put("ok", true);
        resp.put("mensaje", "ELM327 guardado para reconexión futura.");
        resp.put("elmMac", elmMac);
        return resp;
    }
    @GetMapping("/historial/{idVehiculo}")
    public Map<String, Object> historial(@PathVariable Long idVehiculo) {
        Map<String, Object> resp = new LinkedHashMap<>();
        List<Lectura> lecturas = lecturaRepository.findByIdVehiculoOrderByIdLecturaDesc(idVehiculo);
        List<Map<String, Object>> json = new ArrayList<>();
        for (Lectura l : lecturas) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("idLectura", l.getIdLectura());
            m.put("nombreSensor", l.getNombreSensor());
            m.put("tipoSensor", l.getTipoSensor());
            m.put("valor", l.getValor());
            m.put("unidad", l.getUnidad());
            m.put("nivel", l.getNivel());
            m.put("estado", l.getEstado());
            m.put("fechaLectura", String.valueOf(l.getFechaLectura()));
            json.add(m);
        }
        resp.put("ok", true);
        resp.put("lecturas", json);
        return resp;
    }

    @GetMapping("/alertas/{idVehiculo}")
    public Map<String, Object> alertas(@PathVariable Long idVehiculo) {
        Map<String, Object> resp = new LinkedHashMap<>();
        List<Alerta> alertas = alertaRepository.findTop50ByOrderByIdAlertaDesc();
        List<Map<String, Object>> json = new ArrayList<>();
        for (Alerta a : alertas) {
            if (!Objects.equals(a.getIdVehiculo(), idVehiculo)) continue;
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("idAlerta", a.getIdAlerta());
            m.put("nombreSensor", a.getNombreSensor());
            m.put("tipoSensor", a.getTipoSensor());
            m.put("valor", a.getValor());
            m.put("nivel", a.getNivel());
            m.put("tipo", a.getTipo());
            m.put("mensaje", a.getMensaje());
            m.put("leida", a.getLeida() != null && a.getLeida() == 1);
            m.put("fechaAlerta", String.valueOf(a.getFechaAlerta()));
            json.add(m);
        }
        resp.put("ok", true);
        resp.put("alertas", json);
        return resp;
    }

    @GetMapping("/ultima/{idVehiculo}")
    public Map<String, Object> ultima(@PathVariable Long idVehiculo) {
        Map<String, Object> resp = new LinkedHashMap<>();
        List<Lectura> ultimas = lecturaRepository.findTop30ByIdVehiculoOrderByIdLecturaDesc(idVehiculo);
        List<Map<String, Object>> json = new ArrayList<>();
        for (Lectura l : ultimas) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("nombreSensor", l.getNombreSensor());
            m.put("tipoSensor", l.getTipoSensor());
            m.put("valor", l.getValor());
            m.put("unidad", l.getUnidad());
            m.put("nivel", l.getNivel());
            m.put("estado", l.getEstado());
            m.put("fechaLectura", String.valueOf(l.getFechaLectura()));
            json.add(m);
        }
        resp.put("ok", true);
        resp.put("lecturas", json);
        return resp;
    }
    
    @GetMapping("/vehiculo/{id}/elm")
public Map<String, Object> obtenerElm(@PathVariable Long id) {

    Map<String, Object> resp = new LinkedHashMap<>();

    Vehiculo v = vehiculoRepository.findById(id).orElse(null);

    if (v == null) {
        resp.put("ok", false);
        resp.put("mensaje", "Vehículo no encontrado.");
        return resp;
    }

    resp.put("ok", true);
    resp.put("idVehiculo", id);
    resp.put("elmMac", v.getElmMac());

    if (v.getElmMac() == null || v.getElmMac().isBlank()) {
        resp.put("conectado", false);
        resp.put("mensaje", "No hay un ELM327 asociado a este vehículo.");
    } else {
        resp.put("conectado", false);
        resp.put("mensaje", "ELM327 registrado. La conexión Bluetooth debe realizarse desde Android.");
    }

    return resp;
}
  
    // ---------------------------------------------------------
    // CONEXIÓN BLUETOOTH — botón "CONECTAR BLUETOOTH" del dashboard
    // Simula el descubrimiento del escáner ELM327, guarda lecturas
    // reales en "lecturas" y devuelve la telemetría inicial.
    // ---------------------------------------------------------
    @PostMapping("/conectar")
    public Map<String, Object> conectar(Authentication auth) {
        Map<String, Object> resp = new LinkedHashMap<>();
        String correo = auth.getName();

        Cliente cliente = clienteRepository.findByCorreo(correo).orElse(null);
        if (cliente == null) {
            resp.put("ok", false);
            resp.put("mensaje", "Cliente no encontrado. Inicia sesión de nuevo.");
            return resp;
        }

        List<Vehiculo> vehiculos = vehiculoRepository.findByClienteIdCliente(cliente.getIdCliente());
        if (vehiculos.isEmpty()) {
            resp.put("ok", false);
            resp.put("conectado", false);
            resp.put("mensaje", "Primero registra un vehículo para poder conectar el escáner ELM327.");
            return resp;
        }

        Vehiculo v = vehiculos.get(0);
        String elmMac = (v.getElmMac() == null || v.getElmMac().isBlank())
                ? "ELM327-SIM-" + nz(v.getPlaca()) : v.getElmMac();

        resp.put("ok", true);
        resp.put("conectado", true);
        resp.put("idVehiculo", v.getIdVehiculo());
        resp.put("vehiculo", nz(v.getNombreVehiculo()) + " " + nz(v.getPlaca()));
        resp.put("elmMac", elmMac);
        resp.put("mensaje", "Escáner ELM327 conectado por Bluetooth. Recibiendo datos del vehículo en tiempo real.");

        List<Sensor> sensores = sensorRepository.findByVehiculoIdVehiculo(v.getIdVehiculo());
        List<Map<String, Object>> lecturas = new ArrayList<>();
        for (Sensor s : sensores) {
            String tipo = s.getTipoSensor();
            double valor = valorSimulado(tipo);
            String unidad = unidadDe(tipo);

            Lectura l = new Lectura();
            l.setIdVehiculo(v.getIdVehiculo());
            l.setNombreSensor(s.getNombreSensor());
            l.setTipoSensor(tipo);
            l.setValor(valor);
            l.setUnidad(unidad);
            int nivel = calcularNivel(tipo, valor);
            l.setNivel(nivel);
            l.setEstado(nivel < 40 ? "OK" : nivel < 70 ? "ADVERTENCIA" : "FALLA");
            l.setFechaLectura(LocalDateTime.now());
            lecturaRepository.save(l);

            if (nivel >= 40) {
                Alerta a = new Alerta();
                a.setIdVehiculo(v.getIdVehiculo());
                a.setNombreSensor(s.getNombreSensor());
                a.setTipoSensor(tipo);
                a.setValor(valor);
                a.setNivel(nivel);
                a.setTipo(nivel >= 70 ? "falla" : "advertencia");
                a.setMensaje(nivel >= 70
                        ? "Falla crítica en " + s.getNombreSensor() + ": nivel " + nivel + "% (" + valor + " " + unidad + ")."
                        : "Advertencia en " + s.getNombreSensor() + ": nivel " + nivel + "% (" + valor + " " + unidad + ").");
                a.setLeida(0);
                a.setFechaAlerta(LocalDateTime.now());
                alertaRepository.save(a);
                eventPublisher.publishEvent(new AlertaCriticaEvento(this, a));
            }

            Map<String, Object> m = new LinkedHashMap<>();
            m.put("nombreSensor", s.getNombreSensor());
            m.put("tipoSensor", tipo);
            m.put("valor", valor);
            m.put("unidad", unidad);
            m.put("nivel", nivel);
            m.put("estado", l.getEstado());
            lecturas.add(m);
        }

        resp.put("lecturas", lecturas);
        return resp;
    }

    private double valorSimulado(String tipo) {
        return switch (tipo == null ? "" : tipo) {
            case "MAF" ->       redondear(2 + Math.random() * 10);
            case "O2" ->        redondearDos(0.1 + Math.random() * 1.1);
            case "ECT" ->       redondear(75 + Math.random() * 55);
            case "MAP" ->       redondearDos(0.5 + Math.random() * 0.7);
            case "RPM" ->       Math.round(650 + Math.random() * 3800);
            case "VELOCIDAD" -> Math.round(Math.random() * 120);
            case "TEMP" ->      redondear(75 + Math.random() * 55);
            case "OIL" ->       redondearDos(1 + Math.random() * 5);
            case "FUEL" ->      Math.round(15 + Math.random() * 80);
            default ->          redondear(Math.random() * 100);
        };
    }

    private String unidadDe(String tipo) {
        return switch (tipo == null ? "" : tipo) {
            case "RPM" -> "rpm";
            case "VELOCIDAD" -> "km/h";
            case "TEMP", "ECT" -> "°C";
            case "MAF" -> "g/s";
            case "O2" -> "V";
            case "OIL" -> "bar";
            case "FUEL" -> "%";
            default -> "";
        };
    }

    private double redondear(double d) {
        return Math.round(d * 10.0) / 10.0;
    }

    private double redondearDos(double d) {
        return Math.round(d * 100.0) / 100.0;
    }

    private String nz(String s) {
        return s == null ? "" : s;
    }

    private int calcularNivel(String tipoSensor, double valor) {
        double minNormal = 0, maxNormal = 100, maxRango = 100;
        switch (tipoSensor) {
            case "RPM" ->        { minNormal = 600; maxNormal = 3000; maxRango = 7000; }
            case "VELOCIDAD" -> { minNormal = 0;  maxNormal = 100; maxRango = 240; }
            case "TEMP" ->       { minNormal = 80;  maxNormal = 100; maxRango = 130; }
            case "MAF" ->        { minNormal = 2;  maxNormal = 8;   maxRango = 15; }
            case "O2" ->         { minNormal = 0.1; maxNormal = 0.9; maxRango = 1; }
            case "OIL" ->        { minNormal = 1;  maxNormal = 5;   maxRango = 8; }
            case "FUEL" ->       { minNormal = 20; maxNormal = 80;  maxRango = 100; }
            default ->            { minNormal = 0;  maxNormal = 100; maxRango = 100; }
        }
        if (valor <= minNormal) return 0;
        if (valor >= maxNormal) return 100;
        double dentroNormal = maxNormal - minNormal;
        double proporcion = (valor - minNormal) / dentroNormal;
        return (int) Math.round(proporcion * 100);
    }
}