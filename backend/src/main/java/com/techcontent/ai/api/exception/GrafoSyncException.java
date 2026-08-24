package com.techcontent.ai.api.exception;

public class GrafoSyncException extends RuntimeException {
    public GrafoSyncException(String message) {
        super(message);
    }

    public GrafoSyncException(String message, Throwable cause) {
        super(message, cause);
    }
}
