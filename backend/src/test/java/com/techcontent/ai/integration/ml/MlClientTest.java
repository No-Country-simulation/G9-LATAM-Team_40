package com.techcontent.ai.integration.ml;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.client.RestClientTest;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.client.MockRestServiceServer;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

@RestClientTest(MlClient.class)
@TestPropertySource(properties = "ml.service.url=http://ml-test")
class MlClientTest {

    @Autowired
    private MlClient mlClient;

    @Autowired
    private MockRestServiceServer server;

    @Test
    void queryGraphRag_respuestaValida_deberiaDeserializarCorrectamente() {
        String json = """
                {
                  "pregunta": "Texto sobre Java y Spring Boot",
                  "respuesta": "Spring Boot simplifica la creación de aplicaciones Java.",
                  "trazabilidad": [
                    {
                      "documento_id": "doc123",
                      "documento_titulo": "Manual Spring Boot",
                      "categoria": "Backend",
                      "palabras_clave": ["Java", "Spring Boot"],
                      "titulo_seccion": "Introducción",
                      "ruta_jerarquica": ["Capítulo 1"],
                      "nivel": 1,
                      "dominio": "Desarrollo",
                      "score": 0.93,
                      "source_path": "/docs/spring.pdf"
                    }
                  ],
                  "tiempo_segundos": 1.2
                }
                """;

        server.expect(requestTo("http://ml-test/api/v1/query"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

        QueryResponse response = mlClient.queryGraphRag("Texto sobre Java y Spring Boot");

        assertThat(response.respuesta()).isEqualTo("Spring Boot simplifica la creación de aplicaciones Java.");
        assertThat(response.trazabilidad()).hasSize(1);

        TrazabilidadSeccionDto trazabilidad = response.trazabilidad().get(0);
        assertThat(trazabilidad.categoria()).isEqualTo("Backend");
        assertThat(trazabilidad.score()).isEqualTo(0.93);
        assertThat(trazabilidad.palabrasClave()).containsExactly("Java", "Spring Boot");

        server.verify();
    }

    @Test
    void queryGraphRag_errorDelServidor_deberiaLanzarMlServiceException() {
        server.expect(requestTo("http://ml-test/api/v1/query"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(withServerError());

        assertThatThrownBy(() -> mlClient.queryGraphRag("texto de prueba"))
                .isInstanceOf(MlServiceException.class)
                .hasMessageContaining("error");

        server.verify();
    }

    @Test
    void queryGraphRag_servidorNoDisponible_deberiaLanzarMlServiceException() {
        server.expect(requestTo("http://ml-test/api/v1/query"))
                .andRespond(withException(new java.io.IOException("Connection refused")));

        assertThatThrownBy(() -> mlClient.queryGraphRag("texto de prueba"))
                .isInstanceOf(MlServiceException.class)
                .hasMessageContaining("conectar");

        server.verify();
    }
}