package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.response.GrafoResponse;
import com.techcontent.ai.domain.model.Grafo;
import com.techcontent.ai.domain.repository.GrafoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class GrafoServiceTest {

    @Mock
    private GrafoRepository repository;

    @Mock
    private OciStorageClient ociStorageClient;

    private ObjectMapper objectMapper;
    private GrafoService grafoService;

    private final String testBucket = "test-dataset-bucket";
    private final String testPrefix = "prod";

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        grafoService = new GrafoService(repository, objectMapper, ociStorageClient);

        ReflectionTestUtils.setField(grafoService, "datasetBucket", testBucket);
        ReflectionTestUtils.setField(grafoService, "ociPrefix", testPrefix);
    }

    @Test
    @DisplayName("Debe sincronizar e insertar correctamente un grafo desde OCI")
    void sincronizarDesdeOci_Exito() {
        String jsonMock = "{\"nodos\":[{\"id\":\"node1\"}]}";
        InputStream inputStream = new ByteArrayInputStream(jsonMock.getBytes(StandardCharsets.UTF_8));

        UUID generatedId = UUID.randomUUID();
        Grafo grafoGuardado = Grafo.builder()
                .id(generatedId)
                .jsonData(jsonMock)
                .fechaCreacion(LocalDateTime.now())
                .build();

        String expectedPath = "prod/output_json/grafo_nodos_subnodos_graphrag.json";

        when(ociStorageClient.download(eq(testBucket), eq(expectedPath)))
                .thenReturn(inputStream);
        when(repository.save(any(Grafo.class))).thenReturn(grafoGuardado);

        GrafoResponse response = grafoService.sincronizarDesdeOci(null);

        assertThat(response).isNotNull();
        assertThat(response.id()).isEqualTo(generatedId.toString());
        assertThat(response.jsonData()).isInstanceOf(JsonNode.class);

        ArgumentCaptor<Grafo> grafoCaptor = ArgumentCaptor.forClass(Grafo.class);
        verify(repository).save(grafoCaptor.capture());
        assertThat(grafoCaptor.getValue().getJsonData()).isEqualTo(jsonMock);
    }

    @Test
    @DisplayName("Debe retornar el ultimo grafo guardado")
    void obtenerUltimo_Exito() {
        Grafo grafo = Grafo.builder()
                .id(UUID.randomUUID())
                .jsonData("{\"test\": true}")
                .fechaCreacion(LocalDateTime.now())
                .build();

        when(repository.findFirstByOrderByFechaCreacionDesc()).thenReturn(Optional.of(grafo));

        GrafoResponse response = grafoService.obtenerUltimo();

        assertThat(response).isNotNull();
        assertThat(response.id()).isEqualTo(grafo.getId().toString());
    }

    @Test
    @DisplayName("Debe obtener un grafo por su ID")
    void obtenerPorId_Exito() {
        UUID id = UUID.randomUUID();
        Grafo grafo = Grafo.builder()
                .id(id)
                .jsonData("{\"test\": true}")
                .fechaCreacion(LocalDateTime.now())
                .build();

        when(repository.findById(id)).thenReturn(Optional.of(grafo));

        GrafoResponse response = grafoService.obtenerPorId(id);

        assertThat(response).isNotNull();
        assertThat(response.id()).isEqualTo(id.toString());
    }

    @Test
    @DisplayName("Debe retornar la lista de historial paginada con jsonData en null")
    void obtenerHistorial_Exito() {
        UUID id = UUID.randomUUID();
        LocalDateTime fecha = LocalDateTime.now();
        Pageable pageable = PageRequest.of(0, 10);

        GrafoRepository.GrafoResumenProjection projectionMock = mock(GrafoRepository.GrafoResumenProjection.class);
        when(projectionMock.getId()).thenReturn(id);
        when(projectionMock.getFechaCreacion()).thenReturn(fecha);

        Page<GrafoRepository.GrafoResumenProjection> pageResult = new PageImpl<>(List.of(projectionMock));
        when(repository.findAllResumen(pageable)).thenReturn(pageResult);

        Page<GrafoResponse> result = grafoService.obtenerHistorial(pageable);

        assertThat(result).isNotNull();
        assertThat(result.getContent()).hasSize(1);
        assertThat(result.getContent().get(0).id()).isEqualTo(id.toString());
        assertThat(result.getContent().get(0).jsonData()).isNull();
    }

    @Test
    @DisplayName("Debe lanzar EntityNotFoundException si no existe ultimo grafo")
    void obtenerUltimo_NotFound() {
        when(repository.findFirstByOrderByFechaCreacionDesc()).thenReturn(Optional.empty());

        assertThatThrownBy(() -> grafoService.obtenerUltimo())
                .isInstanceOf(EntityNotFoundException.class)
                .hasMessageContaining("No se encontró ningún grafo procesado en el sistema");
    }

    @Test
    @DisplayName("Debe buscar grafos dentro del rango de fechas especificado")
    void buscarPorRangoFechas_Exito() {

        LocalDate desde = LocalDate.of(2026, 1, 1);
        LocalDate hasta = LocalDate.of(2026, 8, 20);

        LocalDateTime desdeExpected = desde.atStartOfDay(); // 2026-01-01T00:00:00
        LocalDateTime hastaExpected = hasta.atTime(LocalTime.MAX); // 2026-08-20T23:59:59.999999999

        Grafo grafo = Grafo.builder()
                .id(UUID.randomUUID())
                .jsonData("{\"test\": true}")
                .fechaCreacion(LocalDateTime.of(2026, 5, 10, 12, 0))
                .build();

        when(repository.findByFechaCreacionBetweenOrderByFechaCreacionDesc(desdeExpected, hastaExpected))
                .thenReturn(List.of(grafo));

        List<GrafoResponse> resultado = grafoService.buscarPorRangoFechas(desde, hasta);

        assertThat(resultado).isNotNull().hasSize(1);
        assertThat(resultado.get(0).id()).isEqualTo(grafo.getId().toString());

        verify(repository).findByFechaCreacionBetweenOrderByFechaCreacionDesc(desdeExpected, hastaExpected);
    }
}