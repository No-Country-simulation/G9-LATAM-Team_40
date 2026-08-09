package com.techcontent.ai.integration.ml;

import com.techcontent.ai.dto.MlRequest;
import com.techcontent.ai.dto.MlResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class MlClient {

    private final RestClient restClient;

    public MlClient(RestClient.Builder restClientBuilder, 
                    @Value("${ml.service.url:http://ml-service:5000}") String mlServiceUrl) {
        this.restClient = restClientBuilder
                .baseUrl(mlServiceUrl)
                .defaultHeader("Content-Type", MediaType.APPLICATION_JSON_VALUE)
                .build();
    }

    public MlResponse predecir(String texto) {
        MlRequest request = MlRequest.builder().texto(texto).build();

        return this.restClient.post()
                .uri("/predict")
                .body(request)
                .retrieve()
                .body(MlResponse.class);
    }
}
