package com.techcontent.ai.api.dto.response;

import java.time.LocalDateTime;

public record ArchivoResponse(
        String id,
        String nombre,
        String url,
        Long tamano,
        String tipo,
        LocalDateTime subidoEn
) {}
