package com.techcontent.ai.dto;

import java.time.LocalDateTime;

public record ContenidoResponse(
    Long id,
    String titulo,
    String texto,
    String autor,
    LocalDateTime fechaCreacion
) {}