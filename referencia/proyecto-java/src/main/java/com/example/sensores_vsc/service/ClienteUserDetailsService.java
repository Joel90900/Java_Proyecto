package com.example.sensores_vsc.service;
import com.example.sensores_vsc.model.Cliente;
import com.example.sensores_vsc.repository.ClienteRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class ClienteUserDetailsService implements UserDetailsService {

    @Autowired
    private ClienteRepository clienteRepository;

    @Override
    public UserDetails loadUserByUsername(String correo) throws UsernameNotFoundException {
        Cliente cliente = clienteRepository.findByCorreo(correo)
            .orElseThrow(() -> new UsernameNotFoundException("Cliente no encontrado"));
        if ("bloqueado".equals(cliente.getEstado())) {
            throw new UsernameNotFoundException("Cliente bloqueado");
        }
        return User.builder()
            .username(correo)
            .password(cliente.getContrasena())
            .roles("CLIENTE")
            .build();
    }
}
