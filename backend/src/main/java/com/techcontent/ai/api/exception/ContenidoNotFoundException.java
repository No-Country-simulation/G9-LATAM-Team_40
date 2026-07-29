package com.techcontent.ai.api.exception;

import java.util.UUID;

public class ContenidoNotFoundException extends RuntimeException {
    public ContenidoNotFoundException(UUID id) {
        super("Contenido no encontrado con id: " + id);
    }
}
