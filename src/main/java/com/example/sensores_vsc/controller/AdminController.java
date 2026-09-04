package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.model.Sensor;
import com.example.sensores_vsc.model.Vehiculo;
import com.example.sensores_vsc.repository.ClienteRepository;
import com.example.sensores_vsc.repository.SensorRepository;
import com.example.sensores_vsc.repository.UsuarioRepository;
import com.example.sensores_vsc.repository.VehiculoRepository;
import com.itextpdf.text.BaseColor;
import com.itextpdf.text.Document;
import com.itextpdf.text.DocumentException;
import com.itextpdf.text.Element;
import com.itextpdf.text.Font;
import com.itextpdf.text.FontFactory;
import com.itextpdf.text.Image;
import com.itextpdf.text.PageSize;
import com.itextpdf.text.Paragraph;
import com.itextpdf.text.Phrase;
import com.itextpdf.text.pdf.PdfPCell;
import com.itextpdf.text.pdf.PdfPTable;
import com.itextpdf.text.pdf.PdfWriter;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

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

    // ---------------------------------------------------------
    // PALETA DE COLORES AUTOSEN
    // ---------------------------------------------------------
    private static final BaseColor NEGRO = new BaseColor(13, 13, 15);
    private static final BaseColor AZUL_OSCURO = new BaseColor(15, 32, 61);
    private static final BaseColor AZUL_MEDIO = new BaseColor(41, 98, 168);
    private static final BaseColor BLANCO = BaseColor.WHITE;
    private static final BaseColor VERDE = new BaseColor(46, 184, 120);
    private static final BaseColor GRIS_CLARO = new BaseColor(240, 243, 247);
    private static final BaseColor GRIS_TEXTO = new BaseColor(90, 96, 105);

    private static final String LOGO_PATH = "static/images/logo-autosen.png";

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

    @GetMapping("/reportes")
    public String reportes(Model model) {
        cargarDatosReportes(model);
        return "admin/reportes";
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

    @GetMapping("/reportes/pdf")
    public void exportarPdfCompleto(HttpServletResponse response) throws Exception {
        response.setContentType("application/pdf");
        response.setHeader("Content-Disposition", "attachment; filename=reporte-autosen.pdf");

        List<Cliente> clientes = clienteRepository.findAll();
        List<Sensor> sensores = sensorRepository.findAll();

        Document doc = new Document(PageSize.A4.rotate(), 30, 30, 30, 30);
        PdfWriter.getInstance(doc, response.getOutputStream());
        doc.open();
        agregarEncabezado(doc, "REPORTE GENERAL AUTOSEN");
        agregarFecha(doc);
        agregarTablaClientes(doc, clientes);
        agregarTablaSensores(doc, sensores);
        doc.close();
    }

    @GetMapping("/reportes/cliente/{id}/pdf")
    public void exportarPdfCliente(@PathVariable Long id, HttpServletResponse response) throws Exception {
        Cliente cliente = clienteRepository.findById(id).orElseThrow();
        response.setContentType("application/pdf");
        response.setHeader("Content-Disposition",
            "attachment; filename=reporte-" + cliente.getNombreCliente().toLowerCase() + ".pdf");

        Document doc = new Document(PageSize.A4, 30, 30, 30, 30);
        PdfWriter.getInstance(doc, response.getOutputStream());
        doc.open();
        agregarEncabezado(doc, cliente.getNombreCliente() + " " + cliente.getApellidoCliente());
        agregarFecha(doc);

        if (cliente.getVehiculos() != null) {
            for (Vehiculo v : cliente.getVehiculos()) {
                Font fontVeh = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 13, AZUL_OSCURO);
                Font fontSub = FontFactory.getFont(FontFactory.HELVETICA, 10, GRIS_TEXTO);
                doc.add(new Paragraph("\n" + v.getNombreVehiculo() + " \u2014 " + v.getMarca(), fontVeh));
                doc.add(new Paragraph("Placa: " + v.getPlaca() + "   |   Color: " + v.getColor(), fontSub));

                if (v.getSensores() != null && !v.getSensores().isEmpty()) {
                    PdfPTable tabla = new PdfPTable(5);
                    tabla.setWidthPercentage(100);
                    tabla.setSpacingBefore(8f);
                    tabla.setSpacingAfter(10f);
                    agregarCabecera(tabla, new String[]{"Sensor", "Tipo", "Nivel", "Estado", "Tipo Da\u00f1o"});
                    boolean par = false;
                    for (Sensor s : v.getSensores()) {
                        String estado = s.getNivel() < 40 ? "OK" : s.getNivel() < 70 ? "ADVERTENCIA" : "FALLA";
                        agregarFila(tabla, par, s.getNombreSensor(), s.getTipoSensor(),
                            s.getNivel() + "%", estado, s.getTipoDano() != null ? s.getTipoDano() : "-");
                        par = !par;
                    }
                    doc.add(tabla);
                }
            }
        }
        doc.close();
    }

    @GetMapping("/reportes/csv/{tipo}")
    public void exportarCsv(@PathVariable String tipo, HttpServletResponse response) throws IOException {
        response.setContentType("text/csv; charset=UTF-8");
        response.setHeader("Content-Disposition", "attachment; filename=reporte-" + tipo + ".csv");
        var writer = response.getWriter();

        switch (tipo) {
            case "clientes" -> {
                writer.println("ID,Nombre,Correo,Estado,Vehiculos");
                for (Cliente c : clienteRepository.findAll()) {
                    writer.printf("%d,%s %s,%s,%s,%d%n",
                        c.getIdCliente(), c.getNombreCliente(), c.getApellidoCliente(),
                        c.getCorreo(), c.getEstado(),
                        c.getVehiculos() != null ? c.getVehiculos().size() : 0);
                }
            }
            case "sensores" -> {
                writer.println("Sensor,Tipo,Nivel,Estado,Vehiculo,Cliente");
                for (Sensor s : sensorRepository.findAll()) {
                    String estado = s.getNivel() < 40 ? "OK" : s.getNivel() < 70 ? "Advertencia" : "Falla";
                    String vehiculo = s.getVehiculo() != null ? s.getVehiculo().getNombreVehiculo() : "-";
                    String cliente = s.getVehiculo() != null && s.getVehiculo().getCliente() != null
                        ? s.getVehiculo().getCliente().getNombreCliente() : "-";
                    writer.printf("%s,%s,%d,%s,%s,%s%n",
                        s.getNombreSensor(), s.getTipoSensor(), s.getNivel(), estado, vehiculo, cliente);
                }
            }
            case "fallas" -> {
                writer.println("Vehiculo,Placa,Cliente,Sensor,Nivel,Tipo Dano");
                for (Sensor s : sensorRepository.findAll()) {
                    if (s.getNivel() >= 70) {
                        String vehiculo = s.getVehiculo() != null ? s.getVehiculo().getNombreVehiculo() : "-";
                        String placa = s.getVehiculo() != null ? s.getVehiculo().getPlaca() : "-";
                        String cliente = s.getVehiculo() != null && s.getVehiculo().getCliente() != null
                            ? s.getVehiculo().getCliente().getNombreCliente() : "-";
                        writer.printf("%s,%s,%s,%s,%d,%s%n",
                            vehiculo, placa, cliente, s.getNombreSensor(), s.getNivel(),
                            s.getTipoDano() != null ? s.getTipoDano() : "-");
                    }
                }
            }
            case "bloqueados" -> {
                writer.println("Nombre,Correo,Vehiculos");
                for (Cliente c : clienteRepository.findAll()) {
                    if ("bloqueado".equals(c.getEstado())) {
                        writer.printf("%s %s,%s,%d%n",
                            c.getNombreCliente(), c.getApellidoCliente(),
                            c.getCorreo(),
                            c.getVehiculos() != null ? c.getVehiculos().size() : 0);
                    }
                }
            }
        }
        writer.flush();
    }

    // ---------------------------------------------------------
    // ENCABEZADO CON LOGO (arriba a la derecha)
    // ---------------------------------------------------------
    private void agregarEncabezado(Document doc, String titulo) throws DocumentException, IOException {
        PdfPTable header = new PdfPTable(2);
        header.setWidthPercentage(100);
        header.setWidths(new float[]{3f, 1f});

        Font fontTitulo = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 20, AZUL_OSCURO);
        PdfPCell celdaTitulo = new PdfPCell(new Phrase(titulo, fontTitulo));
        celdaTitulo.setBorder(0);
        celdaTitulo.setVerticalAlignment(Element.ALIGN_MIDDLE);
        header.addCell(celdaTitulo);

        PdfPCell celdaLogo = new PdfPCell();
        celdaLogo.setBorder(0);
        celdaLogo.setHorizontalAlignment(Element.ALIGN_RIGHT);
        celdaLogo.setVerticalAlignment(Element.ALIGN_MIDDLE);
        try {
            ClassPathResource resource = new ClassPathResource(LOGO_PATH);
            Image logo = Image.getInstance(resource.getURL());
            logo.scaleToFit(60, 60);
            logo.setAlignment(Element.ALIGN_RIGHT);
            celdaLogo.addElement(logo);
        } catch (Exception e) {
            // Si el logo no se encuentra, el PDF se genera igual sin \u00e9l
            celdaLogo.addElement(new Phrase(""));
        }
        header.addCell(celdaLogo);

        doc.add(header);

        // L\u00ednea divisoria de color debajo del encabezado
        PdfPTable linea = new PdfPTable(1);
        linea.setWidthPercentage(100);
        PdfPCell celdaLinea = new PdfPCell();
        celdaLinea.setFixedHeight(3f);
        celdaLinea.setBackgroundColor(VERDE);
        celdaLinea.setBorder(0);
        linea.addCell(celdaLinea);
        linea.setSpacingAfter(10f);
        doc.add(linea);
    }

    private void agregarFecha(Document doc) throws DocumentException {
        Font font = FontFactory.getFont(FontFactory.HELVETICA, 9, GRIS_TEXTO);
        doc.add(new Paragraph("Generado el " +
            LocalDateTime.now().format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm")), font));
        doc.add(new Paragraph("\n"));
    }

    private void agregarCabecera(PdfPTable tabla, String[] columnas) {
        Font font = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 9, BLANCO);
        for (String col : columnas) {
            PdfPCell cell = new PdfPCell(new Phrase(col, font));
            cell.setBackgroundColor(AZUL_OSCURO);
            cell.setPadding(7);
            cell.setBorderColor(NEGRO);
            cell.setBorderWidth(0.5f);
            tabla.addCell(cell);
        }
    }

    /**
     * Agrega una fila con franjas alternadas (blanco / gris claro) y
     * resalta en verde la \u00faltima columna cuando su valor es un estado "OK".
     */
    private void agregarFila(PdfPTable tabla, boolean par, String... valores) {
        BaseColor fondo = par ? GRIS_CLARO : BLANCO;
        Font fontNormal = FontFactory.getFont(FontFactory.HELVETICA, 9, NEGRO);
        for (int i = 0; i < valores.length; i++) {
            String valor = valores[i];
            boolean esColumnaEstado = (i == valores.length - 2); // columna "Estado"
            PdfPCell cell;
            if (esColumnaEstado) {
                BaseColor colorTexto = switch (valor) {
                    case "OK" -> VERDE;
                    case "ADVERTENCIA" -> AZUL_MEDIO;
                    case "FALLA" -> NEGRO;
                    default -> NEGRO;
                };
                Font fontEstado = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 9, colorTexto);
                cell = new PdfPCell(new Phrase(valor, fontEstado));
            } else {
                cell = new PdfPCell(new Phrase(valor, fontNormal));
            }
            cell.setBackgroundColor(fondo);
            cell.setPadding(6);
            cell.setBorderColor(GRIS_CLARO);
            tabla.addCell(cell);
        }
    }

    private void agregarTablaClientes(Document doc, List<Cliente> clientes) throws DocumentException {
        Font fontSeccion = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 13, AZUL_OSCURO);
        doc.add(new Paragraph("CLIENTES", fontSeccion));
        doc.add(new Paragraph("\n"));
        PdfPTable tabla = new PdfPTable(5);
        tabla.setWidthPercentage(100);
        agregarCabecera(tabla, new String[]{"ID", "Nombre", "Correo", "Estado", "Veh\u00edculos"});
        boolean par = false;
        Font fontNormal = FontFactory.getFont(FontFactory.HELVETICA, 9, NEGRO);
        for (Cliente c : clientes) {
            BaseColor fondo = par ? GRIS_CLARO : BLANCO;
            BaseColor colorEstado = "activo".equals(c.getEstado()) ? VERDE : NEGRO;
            Font fontEstado = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 9, colorEstado);

            tabla.addCell(celda(String.valueOf(c.getIdCliente()), fontNormal, fondo));
            tabla.addCell(celda(c.getNombreCliente() + " " + c.getApellidoCliente(), fontNormal, fondo));
            tabla.addCell(celda(c.getCorreo(), fontNormal, fondo));
            tabla.addCell(celda(c.getEstado(), fontEstado, fondo));
            tabla.addCell(celda(String.valueOf(c.getVehiculos() != null ? c.getVehiculos().size() : 0), fontNormal, fondo));
            par = !par;
        }
        doc.add(tabla);
        doc.add(new Paragraph("\n"));
    }

    private void agregarTablaSensores(Document doc, List<Sensor> sensores) throws DocumentException {
        Font fontSeccion = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 13, AZUL_OSCURO);
        doc.add(new Paragraph("ESTADO DE SENSORES", fontSeccion));
        doc.add(new Paragraph("\n"));
        PdfPTable tabla = new PdfPTable(6);
        tabla.setWidthPercentage(100);
        agregarCabecera(tabla, new String[]{"Sensor", "Tipo", "Veh\u00edculo", "Cliente", "Nivel", "Estado"});
        boolean par = false;
        Font fontNormal = FontFactory.getFont(FontFactory.HELVETICA, 9, NEGRO);
        for (Sensor s : sensores) {
            String estado = s.getNivel() < 40 ? "OK" : s.getNivel() < 70 ? "ADVERTENCIA" : "FALLA";
            String vehiculo = s.getVehiculo() != null ? s.getVehiculo().getNombreVehiculo() : "-";
            String cliente = s.getVehiculo() != null && s.getVehiculo().getCliente() != null
                ? s.getVehiculo().getCliente().getNombreCliente() : "-";
            BaseColor fondo = par ? GRIS_CLARO : BLANCO;
            BaseColor colorEstado = switch (estado) {
                case "OK" -> VERDE;
                case "ADVERTENCIA" -> AZUL_MEDIO;
                default -> NEGRO;
            };
            Font fontEstado = FontFactory.getFont(FontFactory.HELVETICA_BOLD, 9, colorEstado);

            tabla.addCell(celda(s.getNombreSensor(), fontNormal, fondo));
            tabla.addCell(celda(s.getTipoSensor(), fontNormal, fondo));
            tabla.addCell(celda(vehiculo, fontNormal, fondo));
            tabla.addCell(celda(cliente, fontNormal, fondo));
            tabla.addCell(celda(s.getNivel() + "%", fontNormal, fondo));
            tabla.addCell(celda(estado, fontEstado, fondo));
            par = !par;
        }
        doc.add(tabla);
    }

    private PdfPCell celda(String texto, Font font, BaseColor fondo) {
        PdfPCell cell = new PdfPCell(new Phrase(texto, font));
        cell.setBackgroundColor(fondo);
        cell.setPadding(6);
        cell.setBorderColor(GRIS_CLARO);
        return cell;
    }

    private void cargarDatosReportes(Model model) {
        List<Cliente> clientes = clienteRepository.findAll();
        List<Sensor> sensores = sensorRepository.findAll();
        long totalFallas = sensores.stream().filter(s -> s.getNivel() >= 70).count();
        long totalAdvertencias = sensores.stream().filter(s -> s.getNivel() >= 40 && s.getNivel() < 70).count();
        model.addAttribute("clientes", clientes);
        model.addAttribute("todosSensores", sensores);
        model.addAttribute("clientesBloqueados", clientes.stream()
            .filter(c -> "bloqueado".equals(c.getEstado())).toList());
        model.addAttribute("vehiculosConFallas", vehiculoRepository.findAll().stream()
            .filter(v -> v.getSensores() != null &&
                v.getSensores().stream().anyMatch(s -> s.getNivel() >= 70)).toList());
        model.addAttribute("totalClientes", clientes.size());
        model.addAttribute("totalVehiculos", vehiculoRepository.count());
        model.addAttribute("totalSensores", sensores.size());
        model.addAttribute("totalFallas", totalFallas);
        model.addAttribute("totalAdvertencias", totalAdvertencias);
    }
}