package com.techcontent.ai.api.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ConsultaRequest(
        @NotBlank(message = "La pregunta es requerida")
        @Size(min = 20, message = "La pregunta debe tener al menos 20 caracteres")
        String pregunta
) {}
