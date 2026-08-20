package com.techcontent.ai.integration.ml;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@EnabledIfEnvironmentVariable(
        named = "RUN_ML_DOCKER_TEST",
        matches = "true"
)
class MlClientDockerIntegrationTest {

    @Test
    void queryGraphRag_conServicioDockerReal_retornaRespuestaYTrazabilidad() {

        MlClient mlClient = new MlClient(
                RestClient.builder().requestFactory(new SimpleClientHttpRequestFactory()),
                "http://localhost:5000"
        );

        QueryResponse response = mlClient.queryGraphRag(
                "Cómo desarrollar una API REST con Java y Spring Boot"
        );

        assertNotNull(response);
        assertNotNull(response.respuesta(), "La respuesta del LLM no debe ser nula");
        assertFalse(response.respuesta().isBlank(), "La respuesta del LLM no debe estar vacía");

        assertNotNull(response.trazabilidad(), "La lista de trazabilidad no debe ser nula");
        assertFalse(response.trazabilidad().isEmpty(), "Debe retornar al menos un nodo/sección de trazabilidad");

        TrazabilidadSeccionDto fuente = response.trazabilidad().get(0);
        assertNotNull(fuente.categoria(), "La categoría de la fuente no debe ser nula");
        assertNotNull(fuente.score(), "El score de la fuente no debe ser nulo");
    }
}