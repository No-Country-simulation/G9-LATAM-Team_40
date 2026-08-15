package com.techcontent.ai.domain.repository;

import com.techcontent.ai.domain.model.Archivo;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;
import java.util.UUID;

public interface ArchivoRepository extends JpaRepository<Archivo, UUID> {

    @Query("""
            SELECT a FROM Archivo a
            WHERE a.userId = :userId
              AND LOWER(a.nombre) LIKE LOWER(CONCAT('%', CONCAT(:nombre, '%')))
              AND (:tipo = '' OR a.tipo = :tipo)
            """)
    Page<Archivo> buscarPorUsuario(
            @Param("userId") UUID userId,
            @Param("nombre") String nombre,
            @Param("tipo") String tipo,
            Pageable pageable
    );

    Optional<Archivo> findByIdAndUserId(UUID id, UUID userId);
}
