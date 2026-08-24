package com.techcontent.ai.domain.repository;

import com.techcontent.ai.domain.model.IndiceUsuario;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface IndiceUsuarioRepository extends JpaRepository<IndiceUsuario, UUID> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select i from IndiceUsuario i where i.userId = :userId")
    Optional<IndiceUsuario> findByUserIdForUpdate(@Param("userId") UUID userId);

    List<IndiceUsuario> findAllByOrderByActualizadoEnAsc();
}
