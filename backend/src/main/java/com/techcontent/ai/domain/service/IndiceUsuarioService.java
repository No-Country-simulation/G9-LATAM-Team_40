package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.response.IndiceResponse;
import com.techcontent.ai.domain.model.Archivo;
import com.techcontent.ai.domain.model.IndiceEstado;
import com.techcontent.ai.domain.model.IndiceUsuario;
import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.domain.repository.IndiceUsuarioRepository;
import com.techcontent.ai.integration.ml.IndexDocumentRequest;
import com.techcontent.ai.integration.ml.IndexJobRequest;
import com.techcontent.ai.integration.ml.IndexJobResponse;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.oci.OciStorageClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class IndiceUsuarioService {

    private final IndiceUsuarioRepository indiceRepository;
    private final ArchivoRepository archivoRepository;
    private final MlClient mlClient;
    private final OciStorageClient ociStorageClient;
    private final ObjectMapper objectMapper;

    @Value("${oci.dataset.bucket}")
    private String datasetBucket;

    @Transactional
    public void marcarSucio(UUID userId) {
        IndiceUsuario indice = obtenerOCrear(userId);
        indice.setRequestedGeneration(indice.getRequestedGeneration() + 1);
        if (indice.getEstado() == IndiceEstado.QUEUED || indice.getEstado() == IndiceEstado.RUNNING) {
            indice.setRebuildPendiente(true);
        } else {
            indice.setEstado(IndiceEstado.DIRTY);
            indice.setEtapa("DOWNLOAD");
            indice.setMensaje("El corpus privado cambió y requiere reconstrucción.");
        }
        tocar(indice);
        indiceRepository.save(indice);
    }

    @Transactional
    public IndiceResponse estado(UUID userId) {
        return toResponse(obtenerOCrear(userId));
    }

    @Transactional
    public IndiceResponse reintentar(UUID userId) {
        IndiceUsuario indice = obtenerOCrear(userId);
        indice.setRequestedGeneration(indice.getRequestedGeneration() + 1);
        indice.setEstado(IndiceEstado.DIRTY);
        indice.setRebuildPendiente(true);
        indice.setMensaje("La reconstrucción fue solicitada nuevamente.");
        tocar(indice);
        return toResponse(indiceRepository.save(indice));
    }

    @Transactional
    public void reconciliarTodos() {
        Set<UUID> userIds = new LinkedHashSet<>(archivoRepository.findDistinctUserIds());
        userIds.addAll(indiceRepository.findAll().stream().map(IndiceUsuario::getUserId).toList());
        for (UUID userId : userIds) {
            try {
                reconciliarUsuario(userId);
            } catch (Exception e) {
                log.error("No se pudo reconciliar el índice privado de {}", userId, e);
            }
        }
    }

    @Transactional
    public void reconciliarUsuario(UUID userId) {
        IndiceUsuario indice = obtenerParaReconciliar(userId);
        List<Archivo> indexables = archivoRepository.findIndexableByUserId(userId);

        if (indice.getEstado() == IndiceEstado.IDLE && !indexables.isEmpty()) {
            indice.setRequestedGeneration(Math.max(1L, indice.getRequestedGeneration()));
            indice.setEstado(IndiceEstado.DIRTY);
            indice.setMensaje("Se detectaron archivos privados pendientes de indexar.");
            tocar(indice);
        }

        if (indice.getMlJobId() != null
                && (indice.getEstado() == IndiceEstado.QUEUED || indice.getEstado() == IndiceEstado.RUNNING)) {
            pollJob(indice);
            indiceRepository.save(indice);
            return;
        }

        if (indice.getEstado() == IndiceEstado.DIRTY || indice.getEstado() == IndiceEstado.FAILED) {
            enviarSnapshot(indice, indexables);
            indiceRepository.save(indice);
        }
    }

    private void enviarSnapshot(IndiceUsuario indice, List<Archivo> indexables) {
        long generation = indice.getRequestedGeneration();
        List<IndexDocumentRequest> documentos = indexables.stream()
                .map(a -> new IndexDocumentRequest(
                        a.getId(), a.getDocumentoId(), a.getNombre(), a.getDominio(), a.getObjectName()))
                .toList();
        boolean purge = !archivoRepository.findByUserIdAndPendienteEliminacionTrue(indice.getUserId()).isEmpty();
        indice.setRunningGeneration(generation);
        indice.setDocumentosJson(serializarDocumentos(documentos));
        indice.setMlJobId(null);
        indice.setEstado(IndiceEstado.QUEUED);
        indice.setEtapa("DOWNLOAD");
        indice.setMensaje("Indexación privada en cola.");
        indice.setIniciadoEn(LocalDateTime.now());
        indice.setFinalizadoEn(null);
        tocar(indice);

        IndexJobRequest request = new IndexJobRequest(
                indice.getUserId(),
                generation,
                indice.getUserId() + ":" + generation,
                purge,
                documentos
        );
        try {
            IndexJobResponse job = mlClient.createIndexJob(request);
            if (job == null || job.jobId() == null) {
                throw new IllegalStateException("ML no devolvió job_id para la indexación privada");
            }
            indice.setMlJobId(job.jobId());
            aplicarEstadoJob(indice, job);
        } catch (RuntimeException e) {
            indice.setMensaje("No se pudo crear el job de indexación: " + e.getMessage());
            indice.setEtapa("DOWNLOAD");
            log.warn("Se reintentará la creación del job {} en el siguiente ciclo", request.idempotencyKey(), e);
        }
    }

    private void pollJob(IndiceUsuario indice) {
        IndexJobResponse job = mlClient.getIndexJob(indice.getMlJobId());
        if (job != null) {
            aplicarEstadoJob(indice, job);
        }
    }

    private void aplicarEstadoJob(IndiceUsuario indice, IndexJobResponse job) {
        String status = job.status() == null ? "" : job.status().toUpperCase();
        if ("SUCCEEDED".equals(status) || "SUPERSEDED".equals(status)) {
            finalizarJob(indice, job);
            return;
        }
        if ("FAILED".equals(status)) {
            indice.setEstado(IndiceEstado.FAILED);
            indice.setEtapa(job.stage());
            indice.setMensaje(job.message());
            indice.setFinalizadoEn(LocalDateTime.now());
            tocar(indice);
            return;
        }
        indice.setEstado("RUNNING".equals(status) ? IndiceEstado.RUNNING : IndiceEstado.QUEUED);
        indice.setEtapa(job.stage());
        indice.setMensaje(job.message());
        tocar(indice);
    }

    private void finalizarJob(IndiceUsuario indice, IndexJobResponse job) {
        long jobGeneration = job.generation();
        long runningGeneration = indice.getRunningGeneration() == null ? -1L : indice.getRunningGeneration();
        if (jobGeneration < runningGeneration) {
            indice.setEstado(IndiceEstado.DIRTY);
            indice.setRebuildPendiente(true);
            indice.setMensaje("La generación publicada quedó obsoleta; se solicitará otra.");
            indice.setMlJobId(null);
            tocar(indice);
            return;
        }

        indice.setReleaseId(job.releaseId());
        indice.setMlJobId(null);
        indice.setEtapa("PURGE");
        indice.setMensaje(job.message());
        indice.setFinalizadoEn(LocalDateTime.now());
        try {
            marcarArchivosIndexados(indice);
            indice.setEstado(IndiceEstado.SUCCEEDED);
            boolean needsAnother = indice.getRequestedGeneration() > jobGeneration;
            indice.setRebuildPendiente(needsAnother);
            if (needsAnother) {
                indice.setEstado(IndiceEstado.DIRTY);
                indice.setMensaje("Hay cambios posteriores; se encolará la generación siguiente.");
            }
        } catch (RuntimeException e) {
            indice.setEstado(IndiceEstado.FAILED);
            indice.setMensaje("Release activo, pero falló la limpieza de archivos pendientes: " + e.getMessage());
            log.error("Release privado {} activo con limpieza pendiente fallida", job.releaseId(), e);
        }
        tocar(indice);
    }

    private void marcarArchivosIndexados(IndiceUsuario indice) {
        List<IndexDocumentRequest> snapshot = deserializarDocumentos(indice.getDocumentosJson());
        LocalDateTime now = LocalDateTime.now();
        for (IndexDocumentRequest item : snapshot) {
            archivoRepository.findById(item.archivoId()).ifPresent(archivo -> {
                if (archivo.getUserId().equals(indice.getUserId())) {
                    archivo.setIndexadoEn(now);
                    archivoRepository.save(archivo);
                }
            });
        }

        List<Archivo> pendientes = new ArrayList<>(
                archivoRepository.findByUserIdAndPendienteEliminacionTrue(indice.getUserId()));
        for (Archivo archivo : pendientes) {
            boolean kept = snapshot.stream().anyMatch(item -> item.archivoId().equals(archivo.getId()));
            if (kept) continue;
            if (archivo.getObjectName() != null && !archivo.getObjectName().isBlank()) {
                ociStorageClient.delete(datasetBucket, archivo.getObjectName());
            }
            archivoRepository.delete(archivo);
        }
    }

    private IndiceUsuario obtenerOCrear(UUID userId) {
        return indiceRepository.findById(userId).orElseGet(() -> {
            LocalDateTime now = LocalDateTime.now();
            return indiceRepository.save(IndiceUsuario.builder()
                    .userId(userId)
                    .estado(IndiceEstado.IDLE)
                    .creadoEn(now)
                    .actualizadoEn(now)
                    .build());
        });
    }

    private IndiceUsuario obtenerParaReconciliar(UUID userId) {
        return indiceRepository.findByUserIdForUpdate(userId).orElseGet(() -> {
            LocalDateTime now = LocalDateTime.now();
            return indiceRepository.save(IndiceUsuario.builder()
                    .userId(userId)
                    .estado(IndiceEstado.IDLE)
                    .creadoEn(now)
                    .actualizadoEn(now)
                    .build());
        });
    }

    private void tocar(IndiceUsuario indice) {
        if (indice.getCreadoEn() == null) indice.setCreadoEn(LocalDateTime.now());
        indice.setActualizadoEn(LocalDateTime.now());
    }

    private IndiceResponse toResponse(IndiceUsuario indice) {
        return new IndiceResponse(
                indice.getEstado(), indice.getEtapa(), indice.getMensaje(), indice.getReleaseId(),
                indice.getRunningGeneration(), indice.isRebuildPendiente(), indice.getActualizadoEn()
        );
    }

    private String serializarDocumentos(List<IndexDocumentRequest> documentos) {
        try {
            return objectMapper.writeValueAsString(documentos);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("No se pudo guardar el snapshot de documentos", e);
        }
    }

    private List<IndexDocumentRequest> deserializarDocumentos(String json) {
        if (json == null || json.isBlank()) return List.of();
        try {
            return objectMapper.readValue(json, new TypeReference<>() {});
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Snapshot de documentos de índice malformado", e);
        }
    }
}
