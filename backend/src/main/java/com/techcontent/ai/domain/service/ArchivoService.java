package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.api.dto.response.PaginaResponse;
import com.techcontent.ai.api.exception.ArchivoNotFoundException;
import com.techcontent.ai.domain.model.Archivo;
import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ArchivoService {

    private static final Set<String> TIPOS_PERMITIDOS = Set.of(
            "application/pdf",
            "text/plain",
            "text/markdown"
    );
    private static final Map<String, String> TIPOS_FILTRO = Map.of(
            "pdf", "application/pdf",
            "txt", "text/plain",
            "md", "text/markdown"
    );
    private static final long MAX_TAMANO_BYTES = 10 * 1024 * 1024; // 10 MB

    private final ArchivoRepository archivoRepository;
    private final OciStorageClient ociStorageClient;

    @Value("${oci.dataset.bucket}")
    private String datasetBucket;

    @Value("${oci.prefix:prod}")
    private String ociPrefix;

    public ArchivoResponse subir(MultipartFile file, UUID userId, String categoria) {
        validarArchivo(file);

        String subcarpeta = resolverSubcarpeta(file.getOriginalFilename(), categoria);
        String subcarpetaFormato = resolverFormato(file);

        String objectName = String.format("%s/archivos/%s/%s/%s",
                ociPrefix,
                subcarpeta,
                subcarpetaFormato,
                file.getOriginalFilename()
        );

        try {
            String url = ociStorageClient.upload(
                    datasetBucket,
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

    public PaginaResponse<ArchivoResponse> listar(UUID userId, int page, int size, String q, String tipo) {
        validarPaginacion(page, size);
        String busqueda = normalizarBusqueda(q);
        String tipoMime = normalizarTipo(tipo);

        PageRequest pageable = PageRequest.of(
                page,
                size,
                Sort.by(Sort.Direction.DESC, "subidoEn")
        );
        Page<ArchivoResponse> resultado = archivoRepository
                .buscarPorUsuario(userId, busqueda, tipoMime, pageable)
                .map(this::toResponse);

        return new PaginaResponse<>(
                resultado.getContent(),
                resultado.getNumber(),
                resultado.getSize(),
                resultado.getTotalElements(),
                resultado.getTotalPages()
        );
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
        ociStorageClient.delete(datasetBucket, objectName);
        archivoRepository.delete(archivo);
    }

    private String resolverSubcarpeta(String nombreArchivo, String categoria) {
        if (categoria != null && !categoria.isBlank()) {
            String catUpper = categoria.trim().toUpperCase(Locale.ROOT);
            if ("ISO".equals(catUpper) || "ISOS".equals(catUpper)) {
                return "ISOS";
            }
            if ("LEY".equals(catUpper) || "LEYES".equals(catUpper) || "NORMA".equals(catUpper)) {
                return "LEYES";
            }
        }

        String nombreLower = (nombreArchivo != null) ? nombreArchivo.toLowerCase(Locale.ROOT) : "";
        if (nombreLower.contains("iso") || nombreLower.contains("9001") || nombreLower.contains("14001") || nombreLower.contains("27001")) {
            return "ISOS";
        }

        return "LEYES";
    }

    private String resolverFormato(MultipartFile file) {
        String contentType = file.getContentType();
        String extension = obtenerExtension(file.getOriginalFilename());

        if ("application/pdf".equalsIgnoreCase(contentType) || "pdf".equalsIgnoreCase(extension)) {
            return "pdf";
        }

        if ("text/markdown".equalsIgnoreCase(contentType)
                || "text/plain".equalsIgnoreCase(contentType)
                || "md".equalsIgnoreCase(extension)
                || "txt".equalsIgnoreCase(extension)) {
            return "md";
        }

        return "pdf";
    }

    private String obtenerExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "";
        }
        return filename.substring(filename.lastIndexOf('.') + 1).toLowerCase(Locale.ROOT);
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
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("El archivo no puede estar vacio");
        }
        if (file.getSize() > MAX_TAMANO_BYTES) {
            throw new IllegalArgumentException("El archivo supera el tamano maximo permitido de 10MB");
        }
        if (!TIPOS_PERMITIDOS.contains(file.getContentType())) {
            throw new IllegalArgumentException("Tipo de archivo no permitido. Se aceptan: PDF, TXT, MD");
        }
    }

    private void validarPaginacion(int page, int size) {
        if (page < 0) {
            throw new IllegalArgumentException("El numero de pagina no puede ser negativo");
        }
        if (size < 1 || size > 100) {
            throw new IllegalArgumentException("El tamano de pagina debe estar entre 1 y 100");
        }
    }

    private String normalizarBusqueda(String q) {
        String busqueda = q == null ? "" : q.trim();
        if (busqueda.length() > 100) {
            throw new IllegalArgumentException("La busqueda no puede superar los 100 caracteres");
        }
        return busqueda;
    }

    private String normalizarTipo(String tipo) {
        String alias = tipo == null ? "" : tipo.trim().toLowerCase(Locale.ROOT);
        if (alias.isEmpty()) {
            return "";
        }

        String tipoMime = TIPOS_FILTRO.get(alias);
        if (tipoMime == null) {
            throw new IllegalArgumentException(
                    "Tipo de archivo no permitido. Valores aceptados: pdf, txt, md"
            );
        }
        return tipoMime;
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