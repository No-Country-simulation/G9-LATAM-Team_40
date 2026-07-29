package com.techcontent.ai.integration.ml;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record MlResponse(
        String categoria,
        Double probabilidad,
        @JsonProperty("palabras_clave") List<String> palabrasClave
) {}
