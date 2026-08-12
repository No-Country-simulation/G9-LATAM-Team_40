package com.techcontent.ai.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * DTO para respuesta del servicio de ML (FastAPI)
 * Mapea JSON con nomenclatura snake_case desde FastAPI
 */
public record MlResponse(
        String categoria,
        Double probabilidad,
        @JsonProperty("palabras_clave") List<String> palabrasClave
) {}