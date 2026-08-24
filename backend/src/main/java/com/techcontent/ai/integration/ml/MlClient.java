package com.techcontent.ai.integration.ml;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

import java.util.UUID;

@Slf4j
@Component
public class MlClient {

    private final RestClient restClient;
    private final String internalToken;

    public MlClient(RestClient.Builder builder,
                    @Value("${ml.service.url}") String mlServiceUrl,
                    @Value("${ml.internal.token}") String internalToken) {
        if (internalToken == null || internalToken.isBlank()) {
            throw new IllegalStateException("ML_INTERNAL_TOKEN es obligatorio");
        }
        this.internalToken = internalToken;
        this.restClient = builder
                .baseUrl(mlServiceUrl)
                .build();
    }

    public QueryResponse queryGraphRag(String pregunta, UUID userId) {
        try {
            return restClient.post()
                    .uri("/api/v1/query")
                    .contentType(MediaType.APPLICATION_JSON)
                    .header("X-ML-Internal-Token", internalToken)
                    .body(new QueryRequest(pregunta, userId))
                    .retrieve()
                    .body(QueryResponse.class);
        } catch (HttpServerErrorException e) {
            log.error("El servicio ML respondio con error {}: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new MlServiceException("El servicio de consultas respondio con un error. Intente mas tarde.");
        } catch (ResourceAccessException e) {
            log.error("No se pudo conectar con el servicio ML: {}", e.getMessage());
            throw new MlServiceException("No se pudo conectar con el servicio de consultas.");
        }
    }

    public IndexJobResponse createIndexJob(IndexJobRequest request) {
        try {
            return restClient.post()
                    .uri("/api/v1/index-jobs")
                    .contentType(MediaType.APPLICATION_JSON)
                    .header("X-ML-Internal-Token", internalToken)
                    .body(request)
                    .retrieve()
                    .body(IndexJobResponse.class);
        } catch (HttpServerErrorException e) {
            log.error("El servicio ML fallo al crear el job {}: {}", request.idempotencyKey(), e.getResponseBodyAsString());
            throw new MlServiceException("No se pudo iniciar la indexacion privada.");
        } catch (ResourceAccessException e) {
            log.error("No se pudo conectar con ML al crear el job: {}", e.getMessage());
            throw new MlServiceException("No se pudo conectar con el servicio de indexacion.");
        }
    }

    public IndexJobResponse getIndexJob(UUID jobId) {
        try {
            return restClient.get()
                    .uri("/api/v1/index-jobs/{jobId}", jobId)
                    .header("X-ML-Internal-Token", internalToken)
                    .retrieve()
                    .body(IndexJobResponse.class);
        } catch (HttpServerErrorException e) {
            log.error("El servicio ML fallo al consultar el job {}: {}", jobId, e.getResponseBodyAsString());
            throw new MlServiceException("No se pudo consultar el estado de indexacion.");
        } catch (ResourceAccessException e) {
            throw new MlServiceException("No se pudo conectar con el servicio de indexacion.");
        }
    }

    public IndexGraphResponse getPrivateGraph(UUID userId) {
        try {
            return restClient.get()
                    .uri("/api/v1/indexes/{userId}/graph", userId)
                    .header("X-ML-Internal-Token", internalToken)
                    .retrieve()
                    .body(IndexGraphResponse.class);
        } catch (HttpServerErrorException e) {
            log.error("El servicio ML fallo al consultar el grafo privado {}: {}", userId, e.getResponseBodyAsString());
            throw new MlServiceException("No se pudo consultar el grafo privado.");
        } catch (ResourceAccessException e) {
            throw new MlServiceException("No se pudo conectar con el grafo privado.");
        }
    }
}
