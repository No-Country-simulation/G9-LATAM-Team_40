package com.techcontent.ai.integration.oci;

public class OciStorageTimeoutException extends RuntimeException {

    public OciStorageTimeoutException(String message, Throwable cause) {
        super(message, cause);
    }
}