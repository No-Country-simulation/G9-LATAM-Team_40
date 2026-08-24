package com.techcontent.ai.api.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.LocalDateTime;

public record ArchivoResponse(
        String id,
        String nombre,
        @JsonProperty("documento_id") String documentoId,
        String dominio,
        Long tamano,
        String tipo,
        @JsonProperty("subido_en") LocalDateTime subidoEn,
        @JsonProperty("indexado_en") LocalDateTime indexadoEn,
        @JsonProperty("pendiente_eliminacion") boolean pendienteEliminacion
) {}
