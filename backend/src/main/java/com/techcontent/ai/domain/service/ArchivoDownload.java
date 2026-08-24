package com.techcontent.ai.domain.service;

import java.io.InputStream;

public record ArchivoDownload(
        InputStream contenido,
        long tamano,
        String tipo,
        String nombre
) {}
