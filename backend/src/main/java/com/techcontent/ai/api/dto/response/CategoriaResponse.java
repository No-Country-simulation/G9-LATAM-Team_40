package com.techcontent.ai.api.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

public record CategoriaResponse(
        String nombre,
        @JsonProperty("total_consultas")
        Long totalConsultas
) {}
