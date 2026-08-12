package com.techcontent.ai.domain.repository;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.model.Contenido;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.UUID;

public interface CategoriaRepository extends JpaRepository<Contenido, UUID> {

    @Query("""
            SELECT new com.techcontent.ai.api.dto.response.CategoriaResponse(c.categoria, COUNT(c))
            FROM Contenido c
            GROUP BY c.categoria
            """)
    List<CategoriaResponse> findCategoriasConConteo();
}
