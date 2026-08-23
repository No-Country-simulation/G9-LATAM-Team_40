package com.techcontent.ai.domain.repository;

import com.techcontent.ai.domain.model.Grafo;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

import java.time.LocalDateTime;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
class GrafoRepositoryTest {

    @Autowired
    private GrafoRepository repository;

    @Test
    @DisplayName("Debe retornar la proyección de resumen ordenada por fecha de creación descendente")
    void findAllResumen_Exito() {
        Grafo g1 = Grafo.builder()
                .jsonData("{\"v\": 1}")
                .fechaCreacion(LocalDateTime.now().minusDays(1))
                .build();

        Grafo g2 = Grafo.builder()
                .jsonData("{\"v\": 2}")
                .fechaCreacion(LocalDateTime.now())
                .build();

        repository.save(g1);
        repository.save(g2);

        Page<GrafoRepository.GrafoResumenProjection> result =
                repository.findAllResumen(PageRequest.of(0, 10));

        assertThat(result.getContent()).hasSize(2);
        assertThat(result.getContent().get(0).getId()).isEqualTo(g2.getId());
        assertThat(result.getContent().get(1).getId()).isEqualTo(g1.getId());
    }
}