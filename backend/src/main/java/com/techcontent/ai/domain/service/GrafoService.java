package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.response.GrafoResponse;
import com.techcontent.ai.domain.model.Grafo;
import com.techcontent.ai.domain.repository.GrafoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class GrafoService {

    private final GrafoRepository repository;
    private final ObjectMapper objectMapper;
    private final OciStorageClient ociStorageClient;

    @Value("${oci.dataset.bucket}")
    private String datasetBucket;

    private static final String DEFAULT_OBJECT_NAME = "grafo_nodos_subnodos_graphrag.json";

    @Transactional
    public GrafoResponse sincronizarDesdeOci(String objectName) {
        String nameToFetch = (objectName != null && !objectName.isBlank()) ? objectName : DEFAULT_OBJECT_NAME;

        try (InputStream inputStream = ociStorageClient.download(datasetBucket, nameToFetch)) {
            String jsonContent = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);

            Grafo nuevoGrafo = Grafo.builder()
                    .jsonData(jsonContent)
                    .fechaCreacion(LocalDateTime.now())
                    .build();

            Grafo guardado = repository.save(nuevoGrafo);
            return toResponse(guardado);

        } catch (Exception e) {
            throw new RuntimeException("Error al descargar y procesar el grafo desde OCI Dataset Bucket: " + nameToFetch, e);
        }
    }

    @Transactional(readOnly = true)
    public GrafoResponse obtenerUltimo() {
        Grafo grafo = repository.findFirstByOrderByFechaCreacionDesc()
                .orElseThrow(() -> new EntityNotFoundException("No se encontró ningún grafo procesado en el sistema"));
        return toResponse(grafo);
    }

    @Transactional(readOnly = true)
    public List<GrafoResponse> buscarPorRangoFechas(LocalDateTime desde, LocalDateTime hasta) {
        return repository.findByFechaCreacionBetweenOrderByFechaCreacionDesc(desde, hasta)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<GrafoResponse> obtenerHistorial() {
        return repository.findAll().stream()
                .map(this::toResponse)
                .toList();
    }

    private GrafoResponse toResponse(Grafo grafo) {
        return GrafoResponse.fromEntity(grafo, objectMapper);
    }
}