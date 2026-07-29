package com.techcontent.ai.api.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ContenidoRequest(
        @NotBlank(message = "El titulo es requerido")
        String titulo,

        @NotBlank(message = "El texto es requerido")
        @Size(min = 20, message = "El texto debe tener al menos 20 caracteres")
        String texto
) {}
