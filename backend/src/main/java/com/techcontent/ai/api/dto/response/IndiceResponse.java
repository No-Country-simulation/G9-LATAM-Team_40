package com.techcontent.ai.api.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.techcontent.ai.domain.model.IndiceEstado;

import java.time.LocalDateTime;

public record IndiceResponse(
        IndiceEstado estado,
        String etapa,
        String mensaje,
        @JsonProperty("release_id") String releaseId,
        Long generation,
        @JsonProperty("rebuild_pendiente") boolean rebuildPendiente,
        @JsonProperty("actualizado_en") LocalDateTime actualizadoEn
) {}
