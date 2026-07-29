package com.techcontent.ai.api.dto.request;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;

import java.util.List;

public record ContenidoLoteRequest(
        @NotEmpty(message = "La lista de contenidos no puede estar vacia")
        @Size(max = 20, message = "El lote no puede superar los 20 elementos")
        List<@Valid ContenidoRequest> contenidos
) {}
