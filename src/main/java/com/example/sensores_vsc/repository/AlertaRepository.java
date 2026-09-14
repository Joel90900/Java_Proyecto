package com.example.sensores_vsc.repository;

import com.example.sensores_vsc.model.Alerta;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AlertaRepository extends JpaRepository<Alerta, Long> {
    List<Alerta> findByLeidaOrderByIdAlertaDesc(Integer leida);
    List<Alerta> findTop50ByOrderByIdAlertaDesc();
    long countByLeida(Integer leida);
}