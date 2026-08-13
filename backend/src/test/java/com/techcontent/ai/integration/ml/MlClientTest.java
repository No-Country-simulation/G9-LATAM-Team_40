package com.techcontent.ai.integration.ml;

import com.techcontent.ai.dto.MlResponse;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.client.RestClientTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.test.web.client.match.MockRestRequestMatchers;
import org.springframework.test.web.client.response.MockRestResponseCreators;

import static org.assertj.core.api.Assertions.assertThat;

@RestClientTest(MlClient.class)
@DisplayName("MlClient - Pruebas de integración con servicio ML")
class MlClientTest {

    @Autowired
    private MockRestServiceServer server;

    @Autowired
    private MlClient MlClient;

    @Test
    @DisplayName("Debe retornar respuesta exitosa cuando el servicio ML responde correctamente")
    void testPredictSuccess() {
        // Arrange
        String textoPrueba = "Texto de prueba para clasificar";
        String jsonRespuesta = """
        {
          "categoria": "tecnologia",
          "probabilidad": 0.95,
          "palabras_clave": ["java", "spring"]
        }
        """;


        // Ajustamos la URL para que coincida con la que usa tu propiedad (ml-service:5000)
        server.expect(MockRestRequestMatchers.requestTo(
        "http://localhost:5000/predict"
        )
)
                .andExpect(MockRestRequestMatchers.method(org.springframework.http.HttpMethod.POST))
                .andRespond(MockRestResponseCreators.withSuccess(jsonRespuesta, MediaType.APPLICATION_JSON));

        // Act
        MlResponse response = MlClient.predict(textoPrueba);

        // Assert
        assertNotNull(response);
        assertEquals("tecnologia", response.categoria());
        assertEquals(0.95, response.probabilidad());
        assertEquals(List.of("java", "spring"), response.palabrasClave());
        assertThat(response).isNotNull();


        // Verificamos que se hayan ejecutado todas las expectativas del mock
        server.verify();
    }
}