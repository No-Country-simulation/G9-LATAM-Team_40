package com.techcontent.ai.api.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record ContenidoResponse(
        String id,
        String categoria,
        Double probabilidad,
        List<String> palabrasClave,
        List<ContenidoRelacionadoResponse> contenidosRelacionados,
        LocalDateTime procesadoEn
) {}
