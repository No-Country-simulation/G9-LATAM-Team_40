package com.techcontent.ai.dto;

/**
 * DTO para solicitud al servicio de ML (FastAPI)
 * Estructura: { "texto": "..." }
 */
public record MlRequest(String texto) {}