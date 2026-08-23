package com.techcontent.ai.domain.repository;

import com.techcontent.ai.domain.model.Grafo;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface GrafoRepository extends JpaRepository<Grafo, UUID> {

    Optional<Grafo> findFirstByOrderByFechaCreacionDesc();

    List<Grafo> findByFechaCreacionBetweenOrderByFechaCreacionDesc(LocalDateTime desde, LocalDateTime hasta);

    @Query("SELECT g.id as id, g.fechaCreacion as fechaCreacion FROM Grafo g ORDER BY g.fechaCreacion DESC")
    Page<GrafoResumenProjection> findAllResumen(Pageable pageable);

    interface GrafoResumenProjection {
        UUID getId();
        LocalDateTime getFechaCreacion();
    }
}