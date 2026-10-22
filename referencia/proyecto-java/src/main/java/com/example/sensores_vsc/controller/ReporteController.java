package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.model.Sensor;
import com.example.sensores_vsc.model.Vehiculo;
import com.example.sensores_vsc.repository.ClienteRepository;
import com.example.sensores_vsc.repository.SensorRepository;
import com.example.sensores_vsc.repository.VehiculoRepository;
import com.example.sensores_vsc.patrones.comportamiento.estrategia.ClasificadorEstadoSensor;
import com.example.sensores_vsc.patrones.comportamiento.estrategia.EstadoSensorStrategy;
import com.example.sensores_vsc.patrones.creacional.fabrica.EstadoSensorStrategyFactory;
import com.example.sensores_vsc.patrones.creacional.fabrica.TipoEstado;
import com.example.sensores_vsc.patrones.creacional.singleton.UmbralesReporte;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

@Controller
public class ReporteController {

    // GoF – Factory + Strategy + Singleton
    private static final EstadoSensorStrategy STRATEGY_FILTRO =
            EstadoSensorStrategyFactory.crear(TipoEstado.FILTRO);
    private static final EstadoSensorStrategy STRATEGY_REPORTE =
            EstadoSensorStrategyFactory.crear(TipoEstado.REPORTE);

    @Autowired
    private VehiculoRepository vehiculoRepository;

    @Autowired
    private SensorRepository sensorRepository;

    @Autowired
    private ClienteRepository clienteRepository;

    // ---------------------------------------------------------
    // REPORTES CON FILTROS (/admin/reportes-filtrado)
    // ---------------------------------------------------------
    @GetMapping("/admin/reportes-filtrado")
    public String listaReportes(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String estadoCliente,
            @RequestParam(required = false) String estadoSensor,
            @RequestParam(required = false) String tipoSensor,
            @RequestParam(required = false) String marca,
            @RequestParam(required = false) String tipoPlaca,
            @RequestParam(required = false) Integer nivelMin,
            @RequestParam(required = false) Integer nivelMax,
            @RequestParam(required = false) String ordenarPor,
            Model model) {

        // Normalización defensiva de rangos (nivelMin no debe superar nivelMax)
        if (nivelMin != null && nivelMax != null && nivelMin > nivelMax) {
            int aux = nivelMin;
            nivelMin = nivelMax;
            nivelMax = aux;
        }

        List<Sensor> todos = sensorRepository.findAll();
        List<Sensor> sensoresFiltrados = filtrarSensores(todos, estadoSensor, tipoSensor, nivelMin, nivelMax);
        sensoresFiltrados.sort(comparadorSensores(ordenarPor));

        List<Cliente> todosClientes = clienteRepository.findAll();
        List<Cliente> clientesFiltrados = filtrarClientes(todosClientes, q, estadoCliente, marca);

        long totalFallas = sensoresFiltrados.stream()
                .filter(s -> UmbralesReporte.INSTANCIA.esFalla(nzNivel(s))).count();
        long totalAdvertencias = sensoresFiltrados.stream()
                .filter(s -> UmbralesReporte.INSTANCIA.esAdvertencia(nzNivel(s))).count();

        List<Vehiculo> vehiculosConFallas = vehiculoRepository.findAll().stream()
                .filter(v -> v.getSensores() != null && v.getSensores().stream()
                        .anyMatch(s -> UmbralesReporte.INSTANCIA.esFalla(nzNivel(s))))
                .toList();

        List<Cliente> clientesBloqueados = todosClientes.stream()
                .filter(c -> "bloqueado".equals(c.getEstado())).toList();

        model.addAttribute("clientes", clientesFiltrados);
        model.addAttribute("todosSensores", sensoresFiltrados);
        model.addAttribute("clientesBloqueados", clientesBloqueados);
        model.addAttribute("vehiculosConFallas", vehiculosConFallas);
        model.addAttribute("totalClientes", clientesFiltrados.size());
        model.addAttribute("totalVehiculos", vehiculoRepository.count());
        model.addAttribute("totalSensores", sensoresFiltrados.size());
        model.addAttribute("totalFallas", totalFallas);
        model.addAttribute("totalAdvertencias", totalAdvertencias);

        // Estado de los filtros para repintar el formulario
        model.addAttribute("q", q);
        model.addAttribute("estadoCliente", estadoCliente);
        model.addAttribute("estadoSensor", estadoSensor);
        model.addAttribute("tipoSensor", tipoSensor);
        model.addAttribute("marca", marca);
        model.addAttribute("tipoPlaca", tipoPlaca);
        model.addAttribute("nivelMin", nivelMin);
        model.addAttribute("nivelMax", nivelMax);
        model.addAttribute("ordenarPor", ordenarPor);
        model.addAttribute("tiposSensor", tiposSensor(todos));
        model.addAttribute("marcas", marcas());
        model.addAttribute("tiposPlaca", List.of("particular", "publico"));

        return "admin/reportes";
    }

    // ---------------------------------------------------------
    // REPORTE GENERAL (admin/reportes-pdf.html)
    // ---------------------------------------------------------
    @GetMapping("/admin/reportes-pdf")
    public String reporteGeneral(Model model) {

        List<Vehiculo> vehiculos = vehiculoRepository.findAll();
        List<Sensor> sensores = sensorRepository.findAll();

        long sensoresOptimos = 0, sensoresAdvertencia = 0, sensoresFalla = 0;
        for (Sensor s : sensores) {
            String estado = STRATEGY_FILTRO.clasificar(s.getNivel());
            switch (estado) {
                case "optimo" -> sensoresOptimos++;
                case "advertencia" -> sensoresAdvertencia++;
                default -> sensoresFalla++;
            }
        }

        List<Sensor> alertas = sensores.stream()
                .filter(s -> UmbralesReporte.INSTANCIA.esAdvertencia(nzNivel(s))
                        || UmbralesReporte.INSTANCIA.esFalla(nzNivel(s)))
                .toList();

        int total = sensores.size();
        long saludFlota = total == 0 ? 100 : Math.round(sensoresOptimos * 100.0 / total);

        model.addAttribute("vehiculos", vehiculos);
        model.addAttribute("sensores", sensores);
        model.addAttribute("alertas", alertas);
        model.addAttribute("totalVehiculos", vehiculos.size());
        model.addAttribute("totalSensores", total);
        model.addAttribute("saludFlota", saludFlota);
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
            v.setSensores(sensorRepository.findByVehiculoIdVehiculo(v.getIdVehiculo()));
        }

        model.addAttribute("cliente", cliente);
        model.addAttribute("vehiculos", vehiculos);
        model.addAttribute("fechaGeneracion", LocalDateTime.now());
        model.addAttribute("adminNombre", "Administrador");
        model.addAttribute("reporteId", "RPT-" + System.currentTimeMillis());

        return "admin/reporte-cliente-pdf";
    }

    // ---------------------------------------------------------
    // EXPORTACIÓN EXCEL (/admin/reportes/excel) — Apache POI
    // ---------------------------------------------------------
    @GetMapping("/admin/reportes/excel")
    public ResponseEntity<byte[]> exportarExcel(
            @RequestParam(required = false) String q,
            @RequestParam(required = false) String estadoCliente,
            @RequestParam(required = false) String estadoSensor,
            @RequestParam(required = false) String tipoSensor,
            @RequestParam(required = false) String marca,
            @RequestParam(required = false) Integer nivelMin,
            @RequestParam(required = false) Integer nivelMax) throws IOException {

        if (nivelMin != null && nivelMax != null && nivelMin > nivelMax) {
            int aux = nivelMin;
            nivelMin = nivelMax;
            nivelMax = aux;
        }

        List<Cliente> clientes = filtrarClientes(clienteRepository.findAll(), q, estadoCliente, marca);
        List<Sensor> sensores = filtrarSensores(sensorRepository.findAll(), estadoSensor, tipoSensor, nivelMin, nivelMax);
        List<Cliente> bloqueados = clienteRepository.findAll().stream()
                .filter(c -> "bloqueado".equals(c.getEstado())).toList();

        try (Workbook wb = new XSSFWorkbook();
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {

            Sheet hojaClientes = wb.createSheet("Clientes");
            crearFila(hojaClientes, 0, "ID", "Nombre", "Correo", "Estado", "Vehículos");
            int fila = 1;
            for (Cliente c : clientes) {
                crearFila(hojaClientes, fila++,
                        c.getIdCliente(),
                        nr(c.getNombreCliente()) + " " + nr(c.getApellidoCliente()),
                        nr(c.getCorreo()),
                        nr(c.getEstado()),
                        c.getVehiculos() != null ? c.getVehiculos().size() : 0);
            }

            Sheet hojaSensores = wb.createSheet("Sensores");
            crearFila(hojaSensores, 0, "Sensor", "Tipo", "Vehículo", "Cliente", "Nivel", "Estado", "Diagnóstico");
            fila = 1;
            for (Sensor s : sensores) {
                Vehiculo v = s.getVehiculo();
                String cliente = v != null && v.getCliente() != null
                        ? nr(v.getCliente().getNombreCliente()) + " " + nr(v.getCliente().getApellidoCliente())
                        : "-";
                crearFila(hojaSensores, fila++,
                        nr(s.getNombreSensor()),
                        nr(s.getTipoSensor()),
                        v != null ? nr(v.getNombreVehiculo()) : "-",
                        cliente,
                        s.getNivel() == null ? 0 : s.getNivel(),
                        STRATEGY_REPORTE.clasificar(s.getNivel()),
                        nr(s.getTipoDano()));
            }

            Sheet hojaFallas = wb.createSheet("Vehículos con fallas");
            crearFila(hojaFallas, 0, "Vehículo", "Placa", "Cliente");
            fila = 1;
            for (Vehiculo v : vehiculoRepository.findAll()) {
                if (v.getSensores() != null && v.getSensores().stream()
                        .anyMatch(s -> UmbralesReporte.INSTANCIA.esFalla(nzNivel(s)))) {
                    String cl = v.getCliente() != null
                            ? nr(v.getCliente().getNombreCliente()) + " " + nr(v.getCliente().getApellidoCliente())
                            : "-";
                    crearFila(hojaFallas, fila++, nr(v.getNombreVehiculo()), nr(v.getPlaca()), cl);
                }
            }

            Sheet hojaBloqueados = wb.createSheet("Clientes bloqueados");
            crearFila(hojaBloqueados, 0, "Nombre", "Correo", "Vehículos");
            fila = 1;
            for (Cliente c : bloqueados) {
                crearFila(hojaBloqueados, fila++,
                        nr(c.getNombreCliente()) + " " + nr(c.getApellidoCliente()),
                        nr(c.getCorreo()),
                        c.getVehiculos() != null ? c.getVehiculos().size() : 0);
            }

            wb.write(out);
            return ResponseEntity.ok()
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=reporte-autosen.xlsx")
                    .contentType(MediaType.parseMediaType(
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))
                    .body(out.toByteArray());
        }
    }

    // ---------------------------------------------------------
    // HELPERS DE FILTRADO (patrón Strategy para el estado)
    // ---------------------------------------------------------
    private List<Sensor> filtrarSensores(List<Sensor> todos, String estadoSensor, String tipoSensor,
                                         Integer nivelMin, Integer nivelMax) {
        List<Sensor> resultado = new ArrayList<>();
        for (Sensor s : todos) {
            if (estadoSensor != null && !estadoSensor.isBlank()
                    && !estadoSensor.equalsIgnoreCase(STRATEGY_FILTRO.clasificar(s.getNivel()))) continue;
            if (tipoSensor != null && !tipoSensor.isBlank()
                    && !tipoSensor.equals(s.getTipoSensor())) continue;
            if (nivelMin != null && (s.getNivel() == null || s.getNivel() < nivelMin)) continue;
            if (nivelMax != null && (s.getNivel() == null || s.getNivel() > nivelMax)) continue;
            resultado.add(s);
        }
        return resultado;
    }

    private List<Cliente> filtrarClientes(List<Cliente> todos, String q, String estadoCliente, String marca) {
        List<Cliente> resultado = new ArrayList<>();
        for (Cliente c : todos) {
            if (estadoCliente != null && !estadoCliente.isBlank()
                    && !estadoCliente.equalsIgnoreCase(c.getEstado())) continue;
            if (marca != null && !marca.isBlank()) {
                boolean tieneMarca = c.getVehiculos() != null && c.getVehiculos().stream()
                        .anyMatch(v -> marca.equalsIgnoreCase(v.getMarca()));
                if (!tieneMarca) continue;
            }
            if (q != null && !q.isBlank() && !coincide(q, c)) continue;
            resultado.add(c);
        }
        return resultado;
    }

    private boolean coincide(String q, Cliente c) {
        String ql = q.toLowerCase();
        String texto = (nr(c.getNombreCliente()) + " " + nr(c.getApellidoCliente()) + " "
                + nr(c.getCorreo())).toLowerCase();
        if (texto.contains(ql)) return true;
        if (c.getVehiculos() != null) {
            for (Vehiculo v : c.getVehiculos()) {
                if (nr(v.getPlaca()).toLowerCase().contains(ql)
                        || nr(v.getNombreVehiculo()).toLowerCase().contains(ql)) return true;
            }
        }
        return false;
    }

    private Comparator<Sensor> comparadorSensores(String ordenarPor) {
        String o = ordenarPor == null ? "nombre" : ordenarPor;
        return switch (o) {
            case "nivel" -> Comparator.comparingInt((Sensor s) -> nzNivel(s)).reversed();
            case "estado" -> Comparator.comparing(
                    (Sensor s) -> STRATEGY_FILTRO.clasificar(s.getNivel()),
                    Comparator.comparingInt(ReporteController::pesoEstado));
            default -> Comparator.comparing(
                    (Sensor s) -> s.getVehiculo() != null && s.getVehiculo().getCliente() != null
                            ? nr(s.getVehiculo().getCliente().getNombreCliente()) : "");
        };
    }

    private static int pesoEstado(String estado) {
        return switch (estado == null ? "" : estado) {
            case "falla" -> 2;
            case "advertencia" -> 1;
            default -> 0;
        };
    }

    private List<String> tiposSensor(List<Sensor> todos) {
        Set<String> tipos = new LinkedHashSet<>();
        for (Sensor s : todos) if (s.getTipoSensor() != null) tipos.add(s.getTipoSensor());
        return new ArrayList<>(tipos);
    }

    private List<String> marcas() {
        Set<String> marcas = new LinkedHashSet<>();
        for (Vehiculo v : vehiculoRepository.findAll()) if (v.getMarca() != null) marcas.add(v.getMarca());
        return new ArrayList<>(marcas);
    }

    private void crearFila(Sheet hoja, int fila, Object... valores) {
        Row r = hoja.createRow(fila);
        for (int i = 0; i < valores.length; i++) {
            Cell c = r.createCell(i);
            Object v = valores[i];
            if (v == null) c.setCellValue("");
            else if (v instanceof Number num) c.setCellValue(num.doubleValue());
            else c.setCellValue(String.valueOf(v));
        }
    }

    private int nzNivel(Sensor s) {
        return s.getNivel() == null ? 0 : s.getNivel();
    }

    private String nr(String s) {
        return s == null ? "" : s;
    }
}