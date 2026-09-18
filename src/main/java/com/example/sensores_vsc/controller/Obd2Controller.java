package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Alerta;
import com.example.sensores_vsc.model.Lectura;
import com.example.sensores_vsc.model.Vehiculo;
import com.example.sensores_vsc.repository.AlertaRepository;
import com.example.sensores_vsc.repository.LecturaRepository;
import com.example.sensores_vsc.repository.VehiculoRepository;
import org.springframework.beans.factory.annotation.Autowired;
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