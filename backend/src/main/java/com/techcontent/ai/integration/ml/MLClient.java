package com.techcontent.ai.integration.ml;

import com.techcontent.ai.dto.MlRequest;
import com.techcontent.ai.dto.MlResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Component
@Slf4j
public class MLClient {

    private final RestClient restClient;

    @Value("${ml.service.url}")
    private String mlServiceUrl;

    public MLClient(RestClient.Builder restClientBuilder) {
        this.restClient = restClientBuilder.build();
    }

    public MlResponse predict(String texto) {
        try {
            MlRequest request = new MlRequest(texto);

            log.info("Invocando servicio ML: POST {}/predict", mlServiceUrl);
            log.debug("Texto a clasificar: {}", texto);

            MlResponse response = restClient
                    .post()
                    .uri(mlServiceUrl + "/predict")
                    .body(request)
                    .retrieve()
                    .body(MlResponse.class);

            log.info("Respuesta recibida exitosamente del servicio ML");
            return response;

        } catch (RestClientException e) {
            log.error("Error de conexión con el servicio ML en: {}", mlServiceUrl, e);
            throw new RuntimeException("Fallo en la predicción del modelo ML. Servicio: " + mlServiceUrl, e);
        } catch (Exception e) {
            log.error("Error inesperado en MLClient.predict()", e);
            throw new RuntimeException("Error inesperado en predicción del modelo ML", e);
        }
    }

    public MlResponse predecir(String texto) {
        return predict(texto);
    }
}