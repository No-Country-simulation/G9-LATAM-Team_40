package com.techcontent.ai.api.dto.response;

public record ContenidoRelacionadoResponse(
        String id,
        String titulo,
        Double similitud
) {}
