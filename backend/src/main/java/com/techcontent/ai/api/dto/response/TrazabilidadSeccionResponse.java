package com.techcontent.ai.api.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.UUID;

public record TrazabilidadSeccionResponse(
        @JsonProperty("documento_id")
        String documentoId,
        @JsonProperty("documento_titulo")
        String documentoTitulo,
        String categoria,
        @JsonProperty("palabras_clave")
        List<String> palabrasClave,
        @JsonProperty("titulo_seccion")
        String tituloSeccion,
        @JsonProperty("ruta_jerarquica")
        List<String> rutaJerarquica,
        Integer nivel,
        String dominio,
        Double relevancia,
        String corpus,
        @JsonProperty("archivo_id")
        UUID archivoId
) {}
