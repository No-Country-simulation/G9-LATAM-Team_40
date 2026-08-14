package com.techcontent.ai.integration.ml;

import com.techcontent.ai.dto.MlResponse;
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
    void predict_respuestaValida_deberiaDeserializarCorrectamente() {
        String json = """
                {"categoria":"Backend","probabilidad":0.93,"palabras_clave":["Java","Spring Boot"]}
                """;

        server.expect(requestTo("http://ml-test/predict"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

        MlResponse response = mlClient.predict("Texto sobre Java y Spring Boot");

        assertThat(response.categoria()).isEqualTo("Backend");
        assertThat(response.probabilidad()).isEqualTo(0.93);
        assertThat(response.palabrasClave()).containsExactly("Java", "Spring Boot");

        server.verify();
    }

    @Test
    void predict_errorDelServidor_deberiaLanzarMlServiceException() {
        server.expect(requestTo("http://ml-test/predict"))
                .andExpect(method(HttpMethod.POST))
                .andRespond(withServerError());

        assertThatThrownBy(() -> mlClient.predict("texto de prueba"))
                .isInstanceOf(MlServiceException.class)
                .hasMessageContaining("error");

        server.verify();
    }

    @Test
    void predict_servidorNoDisponible_deberiaLanzarMlServiceException() {
        server.expect(requestTo("http://ml-test/predict"))
                .andRespond(withException(new java.io.IOException("Connection refused")));

        assertThatThrownBy(() -> mlClient.predict("texto de prueba"))
                .isInstanceOf(MlServiceException.class)
                .hasMessageContaining("conectar");

        server.verify();
    }
}
