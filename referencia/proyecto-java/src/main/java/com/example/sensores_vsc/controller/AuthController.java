package com.example.sensores_vsc.controller;

import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.repository.ClienteRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
public class AuthController {

    @Autowired
    private ClienteRepository clienteRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @GetMapping("/login")
    public String showLogin() {
        return "paginas/login";
    }

    @GetMapping("/register")
    public String showRegister() {
        return "paginas/register";
    }

    @PostMapping("/register")
    public String register(@RequestParam String nombre,
                           @RequestParam String apellido,
                           @RequestParam String correo,
                           @RequestParam String contrasena,
                           Model model) {

        if (clienteRepository.findByCorreo(correo).isPresent()) {
            model.addAttribute("error", "El correo ya está registrado.");
            return "paginas/register";
        }

        Cliente cliente = new Cliente();
        cliente.setNombreCliente(nombre);
        cliente.setApellidoCliente(apellido);
        cliente.setCorreo(correo);
        cliente.setContrasena(passwordEncoder.encode(contrasena));
        cliente.setEstado("activo");
        clienteRepository.save(cliente);

        return "redirect:/login";
    }


@GetMapping("/")
public String home() {
    return "paginas/index";
}

@GetMapping("/nosotros")
public String nosotros() {
    return "paginas/nosotros";
}

}