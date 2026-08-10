package com.techcontent.ai.integration.ml;

import org.springframework.stereotype.Component;

@Component
public class MlClient {

    public com.techcontent.ai.dto.MlResponse predict(String texto) {
        com.techcontent.ai.dto.MlResponse response = new com.techcontent.ai.dto.MlResponse();
        response.setCategoria("Tecnología y Cloud");
        response.setProbabilidad(0.95);
        response.setPalabrasClave("Java, Oracle Cloud, Spring Boot");
        return response;
    }

    public com.techcontent.ai.dto.MlResponse predecir(String texto) {
        return predict(texto);
    }
}