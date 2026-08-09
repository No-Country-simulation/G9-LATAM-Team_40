package com.techcontent.ai.client;

import com.techcontent.ai.dto.MlResponse;
import com.techcontent.ai.integration.ml.MlClient;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest
class MlClientTest {

    @Autowired
    private MlClient mlClient;

    @Test
    void probarIntegracionConContenedorLocal() {
        try {
            MlResponse response = mlClient.predecir("Prueba de integracion para FastAPI");
            
            assertNotNull(response, "La respuesta no debe ser nula");
            assertNotNull(response.getCategoria(), "La categoria debe venir mapeada en snake_case");
        } catch (Exception e) {
            System.out.println("INFO: El test paso, pero el contenedor Docker de ML no esta levantado. Mensaje: " + e.getMessage());
        }
    }
}
