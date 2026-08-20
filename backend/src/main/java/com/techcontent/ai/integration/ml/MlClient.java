package com.techcontent.ai.integration.ml;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

@Slf4j
@Component
public class MlClient {

    private final RestClient restClient;

    public MlClient(RestClient.Builder builder,
                    @Value("${ml.service.url}") String mlServiceUrl) {
        this.restClient = builder
                .baseUrl(mlServiceUrl)
                .build();
    }

    public QueryResponse queryGraphRag(String textoConsulta) {
        try {
            return restClient.post()
                    .uri("/api/v1/query")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(new QueryRequest(textoConsulta))
                    .retrieve()
                    .body(QueryResponse.class);
        } catch (HttpServerErrorException e) {
            log.error("El servicio ML respondio con error {}: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new MlServiceException("El servicio de clasificacion respondio con un error. Intente mas tarde.");
        } catch (ResourceAccessException e) {
            log.error("No se pudo conectar con el servicio ML: {}", e.getMessage());
            throw new MlServiceException("No se pudo conectar con el servicio de clasificacion.");
        }
    }
}