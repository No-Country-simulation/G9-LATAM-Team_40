package com.techcontent.ai.integration.ml;

import com.techcontent.ai.dto.MlResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestClient;
import org.springframework.http.client.SimpleClientHttpRequestFactory;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@EnabledIfEnvironmentVariable(
        named = "RUN_ML_DOCKER_TEST",
        matches = "true"
)
class MlClientDockerIntegrationTest {

    @Test
    void predict_conServicioDockerReal_retornaPrediccion() {


       
        MlClient mlClient = new MlClient(
             RestClient.builder().requestFactory(new SimpleClientHttpRequestFactory())
        );

        ReflectionTestUtils.setField(
                mlClient,
                "mlServiceUrl",
                "http://localhost:5000"
        );

        MlResponse response = mlClient.predict(
                "Cómo desarrollar una API REST con Java y Spring Boot"
        );

        assertNotNull(response);
        assertEquals("Backend", response.categoria());
        assertEquals(0.89, response.probabilidad());
        assertEquals(
                List.of("Java", "Spring Boot", "API REST"),
                response.palabrasClave()
        );
    }
}