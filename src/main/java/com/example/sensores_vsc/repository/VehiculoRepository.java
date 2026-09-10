package com.example.sensores_vsc.repository;

import com.example.sensores_vsc.model.Vehiculo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface VehiculoRepository extends JpaRepository<Vehiculo, Long> {
    List<Vehiculo> findByClienteIdCliente(Long idCliente);
    Optional<Vehiculo> findByPlaca(String placa);

    /**
     * Recupera todos los vehículos junto con sus sensores y su cliente asociado
     * en una sola consulta JPQL utilizando LEFT JOIN FETCH, eliminando el problema N+1.
     */
    @Query("SELECT DISTINCT v FROM Vehiculo v LEFT JOIN FETCH v.sensores LEFT JOIN FETCH v.cliente")
    List<Vehiculo> findAllConSensoresYCliente();

    /**
     * Recupera los vehículos de un cliente con sus sensores precargados en el Heap en una sola consulta.
     */
    @Query("SELECT DISTINCT v FROM Vehiculo v LEFT JOIN FETCH v.sensores WHERE v.cliente.idCliente = :idCliente")
    List<Vehiculo> findByClienteIdConSensores(@Param("idCliente") Long idCliente);
}