package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.response.GrafoResponse;
import com.techcontent.ai.api.exception.GrafoSyncException;
import com.techcontent.ai.domain.model.Grafo;
import com.techcontent.ai.domain.repository.GrafoRepository;
import com.techcontent.ai.integration.ml.IndexGraphResponse;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.oci.OciStorageClient;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class GrafoService {

    private final GrafoRepository repository;
    private final ObjectMapper objectMapper;
    private final OciStorageClient ociStorageClient;
    private final MlClient mlClient;

    @Value("${oci.dataset.bucket}")
    private String datasetBucket;

    @Value("${oci.prefix:prod}")
    private String ociPrefix;

    @Value("${grafo.local.path:}")
    private String localPath;

    private static final String DEFAULT_FILE_NAME = "grafo_nodos_subnodos_graphrag.json";

    @EventListener(ApplicationReadyEvent.class)
    public void seedFromLocalIfEmpty() {
        try {
            if (repository.count() > 0) return;
            Path local = resolverArchivoLocal(null);
            if (local == null) {
                log.info("No hay grafo persistido ni archivo local para precargar.");
                return;
            }
            persistirJson(Files.readString(local, StandardCharsets.UTF_8));
        } catch (Exception e) {
            log.warn("No se pudo precargar el grafo local: {}", e.getMessage());
        }
    }

    @Transactional
    public GrafoResponse sincronizarDesdeOci(String objectName) {
        try {
            return persistirJson(leerJson(objectName));
        } catch (GrafoSyncException e) {
            throw e;
        } catch (Exception e) {
            throw new GrafoSyncException(
                    "No se pudo obtener el grafo GraphRAG (OCI y archivo local no disponibles).", e);
        }
    }

    public GrafoResponse obtenerPrivado(UUID userId) {
        IndexGraphResponse graph = mlClient.getPrivateGraph(userId);
        if (graph == null || graph.releaseId() == null || graph.jsonData() == null) {
            Map<String, Object> empty = Map.of("grafo_conceptual", Map.of(
                    "nivel_1_categorias", List.of(),
                    "nivel_2_subcategorias", List.of(),
                    "nivel_3_relaciones", List.of()
            ));
            return GrafoResponse.dePrivado(empty, null, null, null, objectMapper);
        }
        return GrafoResponse.dePrivado(
                graph.jsonData(),
                graph.releaseId(),
                graph.generation(),
                parseDateTime(graph.createdAt()),
                objectMapper
        );
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
                .stream().map(this::toResponse).toList();
    }

    @Transactional(readOnly = true)
    public Page<GrafoResponse> obtenerHistorial(Pageable pageable) {
        return repository.findAllResumen(pageable)
                .map(p -> GrafoResponse.deResumen(p.getId().toString(), p.getFechaCreacion()));
    }

    private GrafoResponse persistirJson(String jsonContent) {
        Grafo nuevoGrafo = Grafo.builder()
                .jsonData(jsonContent)
                .fechaCreacion(LocalDateTime.now())
                .build();
        return toResponse(repository.save(nuevoGrafo));
    }

    private String leerJson(String objectName) throws Exception {
        String objectPath = resolverRutaOci(objectName);
        try (InputStream inputStream = ociStorageClient.download(datasetBucket, objectPath)) {
            return new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception ociError) {
            Path local = resolverArchivoLocal(objectName);
            if (local != null) return Files.readString(local, StandardCharsets.UTF_8);
            throw new GrafoSyncException(
                    "No se pudo descargar el grafo desde OCI ni desde el archivo local.", ociError);
        }
    }

    private Path resolverArchivoLocal(String objectName) {
        if (localPath == null || localPath.isBlank()) return null;
        Path configured = Path.of(localPath);
        if (objectName != null && !objectName.isBlank() && !objectName.contains("/")) {
            Path sibling = configured.getParent() == null ? Path.of(objectName) : configured.getParent().resolve(objectName);
            if (Files.isRegularFile(sibling)) return sibling;
        }
        return Files.isRegularFile(configured) ? configured : null;
    }

    private String resolverRutaOci(String objectName) {
        if (objectName != null && !objectName.isBlank()) {
            return objectName.contains("/") ? objectName : String.format("%s/output_json/%s", ociPrefix, objectName);
        }
        return String.format("%s/output_json/%s", ociPrefix, DEFAULT_FILE_NAME);
    }

    private GrafoResponse toResponse(Grafo grafo) {
        return GrafoResponse.fromEntity(grafo, objectMapper);
    }

    private LocalDateTime parseDateTime(String value) {
        if (value == null || value.isBlank()) return null;
        try {
            return LocalDateTime.ofInstant(Instant.parse(value), ZoneOffset.UTC);
        } catch (Exception ignored) {
            try {
                return LocalDateTime.parse(value);
            } catch (Exception ignoredAgain) {
                return null;
            }
        }
    }
}
