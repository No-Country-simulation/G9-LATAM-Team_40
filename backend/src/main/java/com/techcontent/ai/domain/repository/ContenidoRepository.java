package com.techcontent.ai.domain.repository;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.model.Contenido;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface ContenidoRepository extends JpaRepository<Contenido, UUID> {

    List<Contenido> findByUserId(UUID userId);

    @Query("""
            SELECT DISTINCT c FROM Contenido c LEFT JOIN c.palabrasClave pk
            WHERE c.userId = :userId
            AND (LOWER(c.titulo) LIKE LOWER(CONCAT('%', :query, '%'))
                 OR LOWER(pk) LIKE LOWER(CONCAT('%', :query, '%')))
            """)
    List<Contenido> buscarPorKeyword(@Param("query") String query, @Param("userId") UUID userId);

    @Query("""
            SELECT new com.techcontent.ai.api.dto.response.CategoriaResponse(c.categoria, COUNT(c))
            FROM Contenido c
            GROUP BY c.categoria
            """)
    List<CategoriaResponse> findCategoriasConConteo();
}
