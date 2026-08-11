package com.techcontent.ai.integration.ml;
import com.techcontent.ai.dto.MlRequest;
import com.techcontent.ai.dto.MlResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Component @RequiredArgsConstructor @Slf4j
public class MLClient {
    private final RestClient restClient;
    @Value("${ml.service.url}")
    private String mlServiceUrl;

    public MlResponse predict(String texto) {
        try {
            MlRequest request = new MlRequest(texto);
            return restClient.post().uri(mlServiceUrl + "/predict").body(request).retrieve().body(MlResponse.class);
        } catch (RestClientException e) {
            log.error("Error ML", e);
            throw new RuntimeException("Fallo ML: " + e.getMessage(), e);
        }
    }
    public MlResponse predecir(String texto) { return predict(texto); }
}
