package com.techcontent.ai.domain.repository;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.model.Contenido;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
class CategoriaRepositoryTest {

    @Autowired
    private CategoriaRepository categoriaRepository;

    @Autowired
    private ContenidoRepository contenidoRepository;

    private UUID userId1;
    private UUID userId2;

    @BeforeEach
    void setUp() {
        contenidoRepository.deleteAll();

        userId1 = UUID.randomUUID();
        userId2 = UUID.randomUUID();

        Contenido c1 = Contenido.builder()
                .userId(userId1)
                .categoria("Leyes")
                .titulo("T1")
                .texto("Texto de prueba 1")
                .build();

        Contenido c2 = Contenido.builder()
                .userId(userId1)
                .categoria("Leyes")
                .titulo("T2")
                .texto("Texto de prueba 2")
                .build();

        Contenido c3 = Contenido.builder()
                .userId(userId2)
                .categoria("Salud")
                .titulo("T3")
                .texto("Texto de prueba 3")
                .build();

        contenidoRepository.saveAll(List.of(c1, c2, c3));
    }

    @Test
    void debeContarCategoriasSoloDelUsuarioIndicado() {
        List<CategoriaResponse> resultado = categoriaRepository.findCategoriasConConteoByUserId(userId1);

        assertThat(resultado).hasSize(1);
        assertThat(resultado.get(0).nombre()).isEqualTo("Leyes");
        assertThat(resultado.get(0).totalDocumentos()).isEqualTo(2L);
    }
}