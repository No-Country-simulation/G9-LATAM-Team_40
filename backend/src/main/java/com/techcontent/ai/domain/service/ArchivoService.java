package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.api.exception.ArchivoNotFoundException;
import com.techcontent.ai.domain.model.Archivo;
import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ArchivoService {

    private static final Set<String> TIPOS_PERMITIDOS = Set.of(
            "application/pdf",
            "text/plain",
            "text/markdown",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    );
    private static final long MAX_TAMANO_BYTES = 10 * 1024 * 1024; // 10 MB

    private final ArchivoRepository archivoRepository;
    private final OciStorageClient ociStorageClient;

    @Value("${oci.files.bucket}")
    private String filesBucket;

    public ArchivoResponse subir(MultipartFile file, UUID userId) {
        validarArchivo(file);

        String objectName = userId + "/" + UUID.randomUUID() + "-" + file.getOriginalFilename();

        try {
            // El tamaño (file.getSize()) ha sido agregado aquí como 4to argumento
            String url = ociStorageClient.upload(
                    filesBucket,
                    objectName,
                    file.getInputStream(),
                    file.getSize(),
                    file.getContentType()
            );

            Archivo archivo = Archivo.builder()
                    .userId(userId)
                    .nombre(file.getOriginalFilename())
                    .url(url)
                    .tamano(file.getSize())
                    .tipo(file.getContentType())
                    .subidoEn(LocalDateTime.now())
                    .build();

            return toResponse(archivoRepository.save(archivo));
        } catch (IOException e) {
            throw new RuntimeException("Error al leer el archivo: " + file.getOriginalFilename(), e);
        }
    }

    public List<ArchivoResponse> listar(UUID userId) {
        return archivoRepository.findByUserId(userId).stream()
                .map(this::toResponse)
                .toList();
    }

    public ArchivoResponse obtenerPorId(UUID id, UUID userId) {
        Archivo archivo = archivoRepository.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ArchivoNotFoundException(id));
        return toResponse(archivo);
    }

    public void eliminar(UUID id, UUID userId) {
        Archivo archivo = archivoRepository.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ArchivoNotFoundException(id));

        String objectName = extraerObjectNameDeUrl(archivo.getUrl());
        ociStorageClient.delete(filesBucket, objectName);
        archivoRepository.delete(archivo);
    }

    private String extraerObjectNameDeUrl(String url) {
        if (url == null || url.isBlank()) {
            return "";
        }
        String rawPath;
        if (url.contains("/o/")) {
            rawPath = url.substring(url.indexOf("/o/") + 3);
        } else {
            rawPath = url.substring(url.lastIndexOf('/') + 1);
        }

        return java.net.URLDecoder.decode(rawPath, java.nio.charset.StandardCharsets.UTF_8);
    }

    private void validarArchivo(MultipartFile file) {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("El archivo no puede estar vacio");
        }
        if (file.getSize() > MAX_TAMANO_BYTES) {
            throw new IllegalArgumentException("El archivo supera el tamano maximo permitido de 10MB");
        }
        if (!TIPOS_PERMITIDOS.contains(file.getContentType())) {
            throw new IllegalArgumentException("Tipo de archivo no permitido. Se aceptan: PDF, TXT, MD, DOCX");
        }
    }

    private ArchivoResponse toResponse(Archivo archivo) {
        return new ArchivoResponse(
                archivo.getId().toString(),
                archivo.getNombre(),
                archivo.getUrl(),
                archivo.getTamano(),
                archivo.getTipo(),
                archivo.getSubidoEn()
        );
    }
}