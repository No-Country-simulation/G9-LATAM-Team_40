package com.techcontent.ai.api.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;
import java.util.List;

public record ContenidoResponse(
        String id,
        String categoria,
        Double probabilidad,
        @JsonProperty("palabras_clave")
        List<String> palabrasClave,
        @JsonProperty("contenidos_relacionados")
        List<ContenidoRelacionadoResponse> contenidosRelacionados,
        String respuesta,
        @JsonProperty("procesado_en")
        LocalDateTime procesadoEn
) {}