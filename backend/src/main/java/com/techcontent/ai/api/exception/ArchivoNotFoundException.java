package com.techcontent.ai.api.exception;

import java.util.UUID;

public class ArchivoNotFoundException extends RuntimeException {
    public ArchivoNotFoundException(UUID id) {
        super("Archivo no encontrado con id: " + id);
    }
}
