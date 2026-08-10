package com.techcontent.ai.client;

import com.techcontent.ai.TestConfig;
import com.techcontent.ai.dto.MlResponse;
import com.techcontent.ai.integration.ml.MlClient;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;

import static org.junit.jupiter.api.Assertions.assertNotNull;

@SpringBootTest
@Import(TestConfig.class)
public class MlClientTest {

    @Autowired
    private MlClient mlClient;

    @Test
    public void testPredict() {
        MlResponse response = mlClient.predecir("Texto de prueba para el modelo");
        
        assertNotNull(response);
    }
}