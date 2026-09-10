package com.example.sensores_vsc.repository;

import com.example.sensores_vsc.model.Sensor;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SensorRepository extends JpaRepository<Sensor, Long> {
    List<Sensor> findByVehiculoIdVehiculo(Long idVehiculo);
    List<Sensor> findByEstadoIn(List<String> estados);
    void deleteByVehiculoIdVehiculo(Long idVehiculo);

    /**
     * Consulta personalizada para filtrado multicriterio con JOIN FETCH.
     * Carga en una sola consulta el sensor, su vehículo y el cliente asociado,
     * optimizando el uso de memoria en el Heap de la JVM y eliminando el problema N+1.
     */
    @Query("SELECT s FROM Sensor s LEFT JOIN FETCH s.vehiculo v LEFT JOIN FETCH v.cliente c WHERE " +
           "(:clienteId IS NULL OR c.idCliente = :clienteId) AND " +
           "(:estado IS NULL OR :estado = '' OR LOWER(s.estado) = LOWER(:estado)) AND " +
           "(:tipoSensor IS NULL OR :tipoSensor = '' OR LOWER(s.tipoSensor) = LOWER(:tipoSensor)) AND " +
           "(:busqueda IS NULL OR :busqueda = '' OR " +
           " LOWER(v.nombreVehiculo) LIKE LOWER(CONCAT('%', :busqueda, '%')) OR " +
           " LOWER(v.placa) LIKE LOWER(CONCAT('%', :busqueda, '%')) OR " +
           " LOWER(v.marca) LIKE LOWER(CONCAT('%', :busqueda, '%')) OR " +
           " LOWER(s.nombreSensor) LIKE LOWER(CONCAT('%', :busqueda, '%'))) AND " +
           "(:nivelMin IS NULL OR s.nivel >= :nivelMin) AND " +
           "(:nivelMax IS NULL OR s.nivel <= :nivelMax) " +
           "ORDER BY s.nivel DESC")
    List<Sensor> filtrarSensoresMulticriterio(
            @Param("clienteId") Long clienteId,
            @Param("estado") String estado,
            @Param("tipoSensor") String tipoSensor,
            @Param("busqueda") String busqueda,
            @Param("nivelMin") Integer nivelMin,
            @Param("nivelMax") Integer nivelMax
    );

    @Query("SELECT COUNT(s) FROM Sensor s WHERE LOWER(s.estado) = LOWER(:estado)")
    long countByEstado(@Param("estado") String estado);

    @Query("SELECT COUNT(s) FROM Sensor s WHERE s.nivel >= :nivelMin")
    long countByNivelMayorIgual(@Param("nivelMin") Integer nivelMin);

    @Query("SELECT COUNT(s) FROM Sensor s WHERE s.nivel >= :min AND s.nivel < :max")
    long countByNivelEntre(@Param("min") Integer min, @Param("max") Integer max);

    @Query("SELECT DISTINCT s.tipoSensor FROM Sensor s WHERE s.tipoSensor IS NOT NULL AND s.tipoSensor <> '' ORDER BY s.tipoSensor")
    List<String> findDistinctTiposSensor();
}