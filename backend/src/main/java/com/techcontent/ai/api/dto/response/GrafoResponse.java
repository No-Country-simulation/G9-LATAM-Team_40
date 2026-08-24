package com.techcontent.ai.api.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.domain.model.Grafo;

import java.time.LocalDateTime;

public record GrafoResponse(
        String id,
        @JsonProperty("json_data") Object jsonData,
        @JsonProperty("fecha_creacion") LocalDateTime fechaCreacion,
        String scope,
        @JsonProperty("release_id") String releaseId,
        Long generation
) {
    public static GrafoResponse fromEntity(Grafo grafo, ObjectMapper objectMapper) {
        Object parsedJson;
        try {
            parsedJson = objectMapper.readTree(grafo.getJsonData());
        } catch (Exception e) {
            parsedJson = grafo.getJsonData();
        }
        return new GrafoResponse(
                grafo.getId() == null ? null : grafo.getId().toString(),
                parsedJson,
                grafo.getFechaCreacion(),
                "BASE",
                null,
                null
        );
    }

    public static GrafoResponse dePrivado(Object jsonData, String releaseId, Long generation,
                                          LocalDateTime createdAt, ObjectMapper objectMapper) {
        Object parsedJson = jsonData;
        if (jsonData instanceof String json) {
            try {
                parsedJson = objectMapper.readTree(json);
            } catch (Exception ignored) {
                // The raw string remains available for a malformed private snapshot.
            }
        }
        return new GrafoResponse(null, parsedJson, createdAt, "PRIVATE", releaseId, generation);
    }

    public static GrafoResponse deResumen(String id, LocalDateTime fechaCreacion) {
        return new GrafoResponse(id, null, fechaCreacion, "BASE", null, null);
    }
}
