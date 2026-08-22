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
import org.springframework.test.util.ReflectionTestUtils;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
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

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        grafoService = new GrafoService(repository, objectMapper, ociStorageClient);

        // Inyectamos el valor de la propiedad @Value
        ReflectionTestUtils.setField(grafoService, "datasetBucket", testBucket);
    }

    @Test
    @DisplayName("Debe sincronizar e insertar correctamente un grafo desde OCI")
    void sincronizarDesdeOci_Exito() {
        // Arrange
        String jsonMock = "{\"nodos\":[{\"id\":\"node1\"}]}";
        InputStream inputStream = new ByteArrayInputStream(jsonMock.getBytes(StandardCharsets.UTF_8));

        UUID generatedId = UUID.randomUUID();
        Grafo grafoGuardado = Grafo.builder()
                .id(generatedId)
                .jsonData(jsonMock)
                .fechaCreacion(LocalDateTime.now())
                .build();

        when(ociStorageClient.download(eq(testBucket), eq("grafo_nodos_subnodos_graphrag.json")))
                .thenReturn(inputStream);
        when(repository.save(any(Grafo.class))).thenReturn(grafoGuardado);

        // Act
        GrafoResponse response = grafoService.sincronizarDesdeOci(null);

        // Assert
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
        // Arrange
        Grafo grafo = Grafo.builder()
                .id(UUID.randomUUID())
                .jsonData("{\"test\": true}")
                .fechaCreacion(LocalDateTime.now())
                .build();

        when(repository.findFirstByOrderByFechaCreacionDesc()).thenReturn(Optional.of(grafo));

        // Act
        GrafoResponse response = grafoService.obtenerUltimo();

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.id()).isEqualTo(grafo.getId().toString());
    }

    @Test
    @DisplayName("Debe lanzar EntityNotFoundException si no existe ultimo grafo")
    void obtenerUltimo_NotFound() {
        when(repository.findFirstByOrderByFechaCreacionDesc()).thenReturn(Optional.empty());

        assertThatThrownBy(() -> grafoService.obtenerUltimo())
                .isInstanceOf(EntityNotFoundException.class)
                .hasMessageContaining("No se encontró ningún grafo procesado en el sistema");
    }
}