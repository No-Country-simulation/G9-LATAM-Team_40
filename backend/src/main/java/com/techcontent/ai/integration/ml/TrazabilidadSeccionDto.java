package com.techcontent.ai.integration.ml;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record TrazabilidadSeccionDto(
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
        Double score,

        @JsonProperty("source_path")
        String sourcePath
) {}