package com.techcontent.ai.integration.ml;

import com.techcontent.ai.dto.MlResponse;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.client.RestClientTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.test.web.client.match.MockRestRequestMatchers;
import org.springframework.test.web.client.response.MockRestResponseCreators;

import static org.assertj.core.api.Assertions.assertThat;

@RestClientTest(MLClient.class)
@DisplayName("MLClient - Pruebas de integración con servicio ML")
class MLClientTest {

    @Autowired
    private MockRestServiceServer server;

    @Autowired
    private MLClient mlClient;

    @Test
    @DisplayName("Debe retornar respuesta exitosa cuando el servicio ML responde correctamente")
    void testPredictSuccess() {
        // Arrange
        String textoPrueba = "Texto de prueba para clasificar";
        String jsonRespuesta = "{\"categoria\": \"tecnologia\", \"confianza\": 0.95}";

        // Ajustamos la URL para que coincida con la que usa tu propiedad (ml-service:5000)
        server.expect(MockRestRequestMatchers.requestTo("http://ml-service:5000/predict"))
                .andExpect(MockRestRequestMatchers.method(org.springframework.http.HttpMethod.POST))
                .andRespond(MockRestResponseCreators.withSuccess(jsonRespuesta, MediaType.APPLICATION_JSON));

        // Act
        MlResponse response = mlClient.predict(textoPrueba);

        // Assert
        assertThat(response).isNotNull();

        // Verificamos que se hayan ejecutado todas las expectativas del mock
        server.verify();
    }
}