package com.techcontent.ai.api.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.domain.model.Grafo;

import java.time.LocalDateTime;

public record GrafoResponse(
        String id,
        @JsonProperty("json_data")
        Object jsonData,
        @JsonProperty("fecha_creacion")
        LocalDateTime fechaCreacion
) {
    public static GrafoResponse fromEntity(Grafo grafo, ObjectMapper objectMapper) {
        Object parsedJson;
        try {
            parsedJson = objectMapper.readTree(grafo.getJsonData());
        } catch (Exception e) {
            parsedJson = grafo.getJsonData();
        }

        return new GrafoResponse(
                grafo.getId() != null ? grafo.getId().toString() : null,
                parsedJson,
                grafo.getFechaCreacion()
        );
    }

    public static GrafoResponse deResumen(String id, LocalDateTime fechaCreacion) {
        return new GrafoResponse(id, null, fechaCreacion);
    }
}