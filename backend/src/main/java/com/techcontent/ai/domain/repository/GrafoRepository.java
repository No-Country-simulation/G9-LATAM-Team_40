package com.techcontent.ai.domain.repository;

import com.techcontent.ai.domain.model.Grafo;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface GrafoRepository extends JpaRepository<Grafo, UUID> {

    Optional<Grafo> findFirstByOrderByFechaCreacionDesc();

    List<Grafo> findByFechaCreacionBetweenOrderByFechaCreacionDesc(LocalDateTime desde, LocalDateTime hasta);
}