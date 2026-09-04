package com.example.sensores_vsc.repository;

import com.example.sensores_vsc.model.Sensor;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SensorRepository extends JpaRepository<Sensor, Long> {
    List<Sensor> findByVehiculoIdVehiculo(Long idVehiculo);
    List<Sensor> findByEstadoIn(List<String> estados);
    void deleteByVehiculoIdVehiculo(Long idVehiculo);
}