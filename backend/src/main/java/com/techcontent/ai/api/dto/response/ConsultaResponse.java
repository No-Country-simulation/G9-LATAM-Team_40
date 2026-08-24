package com.techcontent.ai.api.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.LocalDateTime;
import java.util.List;

public record ConsultaResponse(
        String id,
        String pregunta,
        String respuesta,
        @JsonProperty("categoria_fuente_principal")
        String categoriaFuentePrincipal,
        Double relevancia,
        @JsonProperty("palabras_clave")
        List<String> palabrasClave,
        List<TrazabilidadSeccionResponse> trazabilidad,
        @JsonProperty("tiempo_segundos")
        Double tiempoSegundos,
        @JsonProperty("procesado_en")
        LocalDateTime procesadoEn
) {}
