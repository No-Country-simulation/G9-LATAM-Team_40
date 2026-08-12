package com.techcontent.ai.dto;

public record ArchivoResponse(
    Long id,
    String nombreArchivo,
    String tipoContenido,
    String urlAcceso
) {}