package com.techcontent.ai.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ContenidoRequest(
    @NotBlank(message = "El título no puede estar vacío")
    @Size(min = 3, max = 100, message = "El título debe tener entre 3 y 100 caracteres")
    String titulo,

    @NotBlank(message = "El texto o prompt no puede estar vacío")
    @Size(min = 10, max = 1000, message = "El contenido debe tener entre 10 y 1000 caracteres")
    String texto
) {}