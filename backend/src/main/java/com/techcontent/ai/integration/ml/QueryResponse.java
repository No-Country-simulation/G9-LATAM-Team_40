package com.techcontent.ai.integration.ml;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record QueryResponse(
        String pregunta,
        String respuesta,
        List<TrazabilidadSeccionDto> trazabilidad,

        @JsonProperty("tiempo_segundos")
        Double tiempoSegundos
) {}