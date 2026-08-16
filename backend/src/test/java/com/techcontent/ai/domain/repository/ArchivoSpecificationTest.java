package com.techcontent.ai.domain.repository;

import com.techcontent.ai.api.dto.request.ArchivoFiltroDTO;
import com.techcontent.ai.domain.model.Archivo;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDateTime;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@ActiveProfiles("test")
class ArchivoSpecificationTest {

    @Autowired
    private ArchivoRepository archivoRepository;

    private UUID userId1;
    private UUID userId2;

    @BeforeEach
    void setUp() {
        archivoRepository.deleteAll();

        userId1 = UUID.randomUUID();
        userId2 = UUID.randomUUID();

        // Archivo 1: PDF de usuario 1
        Archivo archivo1 = Archivo.builder()
                .userId(userId1)
                .nombre("Manual Técnico de Java.pdf")
                .url("https://oci/bucket/manual.pdf")
                .tamano(2048L)
                .tipo("application/pdf")
                .subidoEn(LocalDateTime.of(2026, 5, 1, 10, 0))
                .build();

        // Archivo 2: TXT de usuario 1
        Archivo archivo2 = Archivo.builder()
                .userId(userId1)
                .nombre("Notas de Arquitectura.txt")
                .url("https://oci/bucket/notas.txt")
                .tamano(512L)
                .tipo("text/plain")
                .subidoEn(LocalDateTime.of(2026, 5, 10, 15, 0))
                .build();

        // Archivo 3: PDF de usuario 2
        Archivo archivo3 = Archivo.builder()
                .userId(userId2)
                .nombre("Manual de Spring Boot.pdf")
                .url("https://oci/bucket/spring.pdf")
                .tamano(4096L)
                .tipo("application/pdf")
                .subidoEn(LocalDateTime.of(2026, 5, 15, 12, 0))
                .build();

        archivoRepository.saveAll(java.util.List.of(archivo1, archivo2, archivo3));
    }

    @Test
    void deberiaFiltrarPorNombreParcial() {
        ArchivoFiltroDTO filtro = new ArchivoFiltroDTO();
        filtro.setNombre("Manual");

        Specification<Archivo> spec = ArchivoSpecification.conFiltros(filtro);
        Page<Archivo> resultado = archivoRepository.findAll(spec, PageRequest.of(0, 10));

        assertThat(resultado.getContent()).hasSize(2);
        assertThat(resultado.getContent()).allMatch(a -> a.getNombre().contains("Manual"));
    }

    @Test
    void deberiaFiltrarPorTipoYUsuario() {
        ArchivoFiltroDTO filtro = new ArchivoFiltroDTO();
        filtro.setUserId(userId1);
        filtro.setTipo("application/pdf");

        Specification<Archivo> spec = ArchivoSpecification.conFiltros(filtro);
        Page<Archivo> resultado = archivoRepository.findAll(spec, PageRequest.of(0, 10));

        assertThat(resultado.getContent()).hasSize(1);
        assertThat(resultado.getContent().get(0).getNombre()).isEqualTo("Manual Técnico de Java.pdf");
    }

    @Test
    void deberiaFiltrarPorRangoDeFechasCombinado() {
        ArchivoFiltroDTO filtro = new ArchivoFiltroDTO();
        filtro.setFechaInicio(LocalDateTime.of(2026, 5, 5, 0, 0));
        filtro.setFechaFin(LocalDateTime.of(2026, 5, 20, 23, 59));

        Specification<Archivo> spec = ArchivoSpecification.conFiltros(filtro);
        Page<Archivo> resultado = archivoRepository.findAll(spec, PageRequest.of(0, 10));

        assertThat(resultado.getContent()).hasSize(2); // Archivo 2 y Archivo 3
    }

    @Test
    void deberiaRetornarTodoCuandoFiltrosEstanVacios() {
        ArchivoFiltroDTO filtro = new ArchivoFiltroDTO();

        Specification<Archivo> spec = ArchivoSpecification.conFiltros(filtro);
        Page<Archivo> resultado = archivoRepository.findAll(spec, PageRequest.of(0, 10));

        assertThat(resultado.getContent()).hasSize(3);
    }
}