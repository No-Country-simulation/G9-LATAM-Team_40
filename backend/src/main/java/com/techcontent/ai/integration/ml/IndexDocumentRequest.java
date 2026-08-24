package com.techcontent.ai.integration.ml;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.UUID;

public record IndexDocumentRequest(
        @JsonProperty("archivo_id") UUID archivoId,
        @JsonProperty("documento_id") String documentoId,
        @JsonProperty("nombre_original") String nombreOriginal,
        String dominio,
        @JsonProperty("object_name") String objectName
) {}
