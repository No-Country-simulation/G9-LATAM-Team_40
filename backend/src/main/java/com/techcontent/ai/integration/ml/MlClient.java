package com.techcontent.ai.integration.ml;

import com.techcontent.ai.dto.MlRequest;
import com.techcontent.ai.dto.MlResponse;
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

    public MlResponse predict(String texto) {
        try {
            return restClient.post()
                    .uri("/predict")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(new MlRequest(texto))
                    .retrieve()
                    .body(MlResponse.class);
        } catch (HttpServerErrorException e) {
            log.error("El servicio ML respondio con error {}: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new MlServiceException("El servicio de clasificacion respondio con un error. Intente mas tarde.");
        } catch (ResourceAccessException e) {
            log.error("No se pudo conectar con el servicio ML: {}", e.getMessage());
            throw new MlServiceException("No se pudo conectar con el servicio de clasificacion.");
        }
    }
}
