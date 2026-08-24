package com.techcontent.ai.integration.ml;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@EnabledIfEnvironmentVariable(named = "RUN_ML_DOCKER_TEST", matches = "true")
class MlClientDockerIntegrationTest {

    @Test
    void queryGraphRag_conServicioDockerReal_retornaRespuestaYTrazabilidad() {
        String token = System.getenv("ML_INTERNAL_TOKEN");
        MlClient mlClient = new MlClient(
                RestClient.builder().requestFactory(new SimpleClientHttpRequestFactory()),
                "http://localhost:5000",
                token
        );
        QueryResponse response = mlClient.queryGraphRag(
                "¿Qué obligaciones de seguridad contiene el corpus normativo?",
                UUID.randomUUID()
        );
        assertNotNull(response);
        assertNotNull(response.respuesta());
        assertFalse(response.respuesta().isBlank());
        assertNotNull(response.trazabilidad());
    }
}
