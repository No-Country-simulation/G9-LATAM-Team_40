package com.techcontent.ai.domain.repository;

import com.techcontent.ai.domain.model.Archivo;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ArchivoRepository extends JpaRepository<Archivo, UUID> {

    List<Archivo> findByUserId(UUID userId);

    Optional<Archivo> findByIdAndUserId(UUID id, UUID userId);
}
