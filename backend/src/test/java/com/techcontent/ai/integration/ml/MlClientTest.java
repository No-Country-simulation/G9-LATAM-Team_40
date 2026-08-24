package com.techcontent.ai.integration.ml;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.client.RestClientTest;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.client.MockRestServiceServer;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.header;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

@RestClientTest(MlClient.class)
@TestPropertySource(properties = {
        "ml.service.url=http://ml-test",
        "ml.internal.token=test-token"
})
class MlClientTest {

    @Autowired
    private MlClient mlClient;

    @Autowired
    private MockRestServiceServer server;

    @Test
    void queryGraphRag_enviaUsuarioYTokenYConservaScore() {
        UUID userId = UUID.fromString("00000000-0000-0000-0000-000000000001");
        String json = """
                {
                  "pregunta": "¿Qué obligaciones de seguridad contiene el corpus?",
                  "respuesta": "Respuesta",
                  "trazabilidad": [{
                    "documento_id": "doc-1",
                    "documento_titulo": "Manual",
                    "categoria": "Seguridad",
                    "palabras_clave": ["riesgo"],
                    "titulo_seccion": "Obligaciones",
                    "ruta_jerarquica": ["Capítulo 1"],
                    "nivel": 1,
                    "dominio": "ISOs",
                    "score": 0.93,
                    "corpus": "BASE",
                    "archivo_id": null
                  }],
                  "tiempo_segundos": 1.2
                }
                """;
        server.expect(requestTo("http://ml-test/api/v1/query"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(header("X-ML-Internal-Token", "test-token"))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(content().json("{\"pregunta\":\"¿Qué obligaciones de seguridad contiene el corpus?\",\"user_id\":\"00000000-0000-0000-0000-000000000001\"}"))
                .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

        QueryResponse response = mlClient.queryGraphRag("¿Qué obligaciones de seguridad contiene el corpus?", userId);

        assertThat(response.trazabilidad()).singleElement().satisfies(trace -> assertThat(trace.score()).isEqualTo(0.93));
        server.verify();
    }
}
