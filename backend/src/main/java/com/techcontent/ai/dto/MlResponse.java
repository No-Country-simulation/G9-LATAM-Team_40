package com.techcontent.ai.dto;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
public record MlResponse(
        String categoria,
        Double probabilidad,
        @JsonProperty("palabras_clave") List<String> palabrasClave
) {}
