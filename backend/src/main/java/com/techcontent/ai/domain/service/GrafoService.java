package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.response.GrafoResponse;
import com.techcontent.ai.domain.model.Grafo;
import com.techcontent.ai.domain.repository.GrafoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class GrafoService {

    private final GrafoRepository repository;
    private final ObjectMapper objectMapper;
    private final OciStorageClient ociStorageClient;

    @Value("${oci.dataset.bucket}")
    private String datasetBucket;

    @Value("${oci.prefix:prod}")
    private String ociPrefix;

    private static final String DEFAULT_FILE_NAME = "grafo_nodos_subnodos_graphrag.json";

    @Transactional
    public GrafoResponse sincronizarDesdeOci(String objectName) {

        String objectPath = resolverRutaOci(objectName);

        try (InputStream inputStream = ociStorageClient.download(datasetBucket, objectPath)) {
            String jsonContent = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);

            Grafo nuevoGrafo = Grafo.builder()
                    .jsonData(jsonContent)
                    .fechaCreacion(LocalDateTime.now())
                    .build();

            Grafo guardado = repository.save(nuevoGrafo);
            return toResponse(guardado);

        } catch (Exception e) {
            throw new RuntimeException("Error al descargar y procesar el grafo desde OCI (" + datasetBucket + " -> " + objectPath + ")", e);
        }
    }

    @Transactional(readOnly = true)
    public GrafoResponse obtenerUltimo() {
        Grafo grafo = repository.findFirstByOrderByFechaCreacionDesc()
                .orElseThrow(() -> new EntityNotFoundException("No se encontró ningún grafo procesado en el sistema"));
        return toResponse(grafo);
    }

    @Transactional(readOnly = true)
    public GrafoResponse obtenerPorId(UUID id) {
        Grafo grafo = repository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("No se encontró el grafo con ID: " + id));
        return toResponse(grafo);
    }

    @Transactional(readOnly = true)
    public List<GrafoResponse> buscarPorRangoFechas(LocalDate desde, LocalDate hasta) {
        LocalDateTime desdeDateTime = desde.atStartOfDay();
        LocalDateTime hastaDateTime = hasta.atTime(LocalTime.MAX);

        return repository.findByFechaCreacionBetweenOrderByFechaCreacionDesc(desdeDateTime, hastaDateTime)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public Page<GrafoResponse> obtenerHistorial(Pageable pageable) {
        return repository.findAllResumen(pageable)
                .map(p -> GrafoResponse.deResumen(
                        p.getId().toString(),
                        p.getFechaCreacion()
                ));
    }

    private String resolverRutaOci(String objectName) {
        if (objectName != null && !objectName.isBlank()) {
            if (objectName.contains("/")) {
                return objectName;
            }
            return String.format("%s/output_json/%s", ociPrefix, objectName);
        }
        return String.format("%s/output_json/%s", ociPrefix, DEFAULT_FILE_NAME);
    }

    private GrafoResponse toResponse(Grafo grafo) {
        return GrafoResponse.fromEntity(grafo, objectMapper);
    }
}