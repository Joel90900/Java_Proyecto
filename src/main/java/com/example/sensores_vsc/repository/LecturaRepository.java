package com.example.sensores_vsc.repository;

import com.example.sensores_vsc.model.Lectura;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface LecturaRepository extends JpaRepository<Lectura, Long> {
    List<Lectura> findTop30ByIdVehiculoOrderByIdLecturaDesc(Long idVehiculo);
    List<Lectura> findByIdVehiculoOrderByIdLecturaDesc(Long idVehiculo);
    long countByIdVehiculo(Long idVehiculo);
}