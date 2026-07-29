package com.techcontent.ai.api.exception;

public record ErrorResponse(
        String error,
        String mensaje
) {}
