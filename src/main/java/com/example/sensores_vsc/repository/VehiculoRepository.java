package com.example.sensores_vsc.repository;

import com.example.sensores_vsc.model.Vehiculo;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface VehiculoRepository extends JpaRepository<Vehiculo, Long> {
    List<Vehiculo> findByClienteIdCliente(Long idCliente);
    Optional<Vehiculo> findByPlaca(String placa);
}