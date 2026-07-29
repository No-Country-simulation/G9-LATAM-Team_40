package com.techcontent.ai.integration.ml;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class MlClient {

    private final RestClient restClient;

    public MlClient(@Value("${ml.service.url}") String mlServiceUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(mlServiceUrl)
                .build();
    }

    public MlResponse predict(String texto) {
        return restClient.post()
                .uri("/predict")
                .contentType(MediaType.APPLICATION_JSON)
                .body(new MlRequest(texto))
                .retrieve()
                .body(MlResponse.class);
    }
}
