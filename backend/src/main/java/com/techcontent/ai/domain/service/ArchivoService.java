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
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.text.Normalizer;
import java.time.LocalDateTime;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class ArchivoService {

    private static final Set<String> TIPOS_PERMITIDOS = Set.of(
            "application/pdf",
            "text/plain",
            "text/markdown"
    );
    private static final Map<String, String> EXTENSIONES_MIME = Map.of(
            "pdf", "application/pdf",
            "txt", "text/plain",
            "md", "text/markdown"
    );
    private static final long MAX_TAMANO_BYTES = 10 * 1024 * 1024;
    private static final Pattern CONTROL = Pattern.compile("[\\p{Cntrl}]");

    private final ArchivoRepository archivoRepository;
    private final OciStorageClient ociStorageClient;
    private final IndiceUsuarioService indiceUsuarioService;

    @Value("${oci.dataset.bucket}")
    private String datasetBucket;

    @Value("${oci.prefix:prod}")
    private String ociPrefix;

    public ArchivoResponse subir(MultipartFile file, UUID userId, String dominio) {
        validarArchivo(file);
        String dominioNormalizado = validarDominio(dominio);
        String nombre = validarNombre(file.getOriginalFilename());
        String extension = obtenerExtension(nombre);
        String stem = nombre.substring(0, nombre.length() - extension.length() - 1);
        UUID archivoId = UUID.randomUUID();
        String documentoId = archivoId + "__" + sanearStem(stem);
        String objectName = String.format(
                "%s/users/%s/input/%s/%s.%s",
                ociPrefix,
                userId,
                dominioNormalizado,
                documentoId,
                extension
        );
        String contentType = tipoEfectivo(file, extension);

        try {
            String internalUrl = ociStorageClient.upload(
                    datasetBucket,
                    objectName,
                    file.getInputStream(),
                    file.getSize(),
                    contentType
            );
            Archivo archivo = Archivo.builder()
                    .id(archivoId)
                    .userId(userId)
                    .nombre(nombre)
                    .url(internalUrl)
                    .documentoId(documentoId)
                    .dominio(dominioNormalizado)
                    .objectName(objectName)
                    .tamano(file.getSize())
                    .tipo(contentType)
                    .subidoEn(LocalDateTime.now())
                    .pendienteEliminacion(false)
                    .build();
            ArchivoResponse response = toResponse(archivoRepository.save(archivo));
            indiceUsuarioService.marcarSucio(userId);
            return response;
        } catch (IOException e) {
            throw new RuntimeException("Error al leer el archivo: " + nombre, e);
        }
    }

    public PaginaResponse<ArchivoResponse> listar(UUID userId, int page, int size, String q, String tipo) {
        validarPaginacion(page, size);
        String busqueda = normalizarBusqueda(q);
        String tipoMime = normalizarTipo(tipo);
        PageRequest pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "subidoEn"));
        Page<ArchivoResponse> resultado = archivoRepository
                .buscarPorUsuario(userId, busqueda, tipoMime, pageable)
                .map(this::toResponse);
        return new PaginaResponse<>(
                resultado.getContent(), resultado.getNumber(), resultado.getSize(),
                resultado.getTotalElements(), resultado.getTotalPages()
        );
    }

    public ArchivoResponse obtenerPorId(UUID id, UUID userId) {
        return toResponse(archivoRepository.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ArchivoNotFoundException(id)));
    }

    public void eliminar(UUID id, UUID userId) {
        Archivo archivo = archivoRepository.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ArchivoNotFoundException(id));
        if (!archivo.isPendienteEliminacion()) {
            archivo.setPendienteEliminacion(true);
            archivoRepository.save(archivo);
            indiceUsuarioService.marcarSucio(userId);
        }
    }

    public ArchivoDownload descargar(UUID id, UUID userId) {
        Archivo archivo = archivoRepository.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ArchivoNotFoundException(id));
        String objectName = archivo.getObjectName();
        if (objectName == null || objectName.isBlank()) {
            objectName = extraerObjectNameDeUrl(archivo.getUrl());
        }
        if (objectName == null || objectName.isBlank()) {
            throw new IllegalArgumentException("El archivo no tiene un objeto de almacenamiento resoluble");
        }
        validarObjectName(objectName);
        return new ArchivoDownload(
                ociStorageClient.download(datasetBucket, objectName),
                archivo.getTamano() == null ? 0L : archivo.getTamano(),
                archivo.getTipo() == null ? "application/octet-stream" : archivo.getTipo(),
                nombreSeguroDescarga(archivo.getNombre())
        );
    }

    private ArchivoResponse toResponse(Archivo archivo) {
        return new ArchivoResponse(
                archivo.getId() == null ? null : archivo.getId().toString(),
                archivo.getNombre(),
                archivo.getDocumentoId(),
                archivo.getDominio(),
                archivo.getTamano(),
                archivo.getTipo(),
                archivo.getSubidoEn(),
                archivo.getIndexadoEn(),
                archivo.isPendienteEliminacion()
        );
    }

    private void validarArchivo(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("El archivo no puede estar vacio");
        }
        if (file.getSize() > MAX_TAMANO_BYTES) {
            throw new IllegalArgumentException("El archivo supera el tamano maximo permitido de 10MB");
        }
        String extension = obtenerExtension(validarNombre(file.getOriginalFilename()));
        String contentType = file.getContentType();
        if (!EXTENSIONES_MIME.containsKey(extension)
                || (contentType != null && !contentType.isBlank() && !TIPOS_PERMITIDOS.contains(contentType))) {
            throw new IllegalArgumentException("Tipo de archivo no permitido. Se aceptan: PDF, TXT, MD");
        }
    }

    private String validarDominio(String dominio) {
        String value = dominio == null ? "" : dominio.trim().toUpperCase(Locale.ROOT);
        if (!"ISOS".equals(value) && !"LEYES".equals(value)) {
            throw new IllegalArgumentException("El dominio es obligatorio y debe ser ISOS o LEYES");
        }
        return value;
    }

    private String validarNombre(String original) {
        String raw = original == null ? "" : original.trim();
        if (raw.isBlank() || raw.contains("..") || raw.contains("/") || raw.contains("\\")
                || CONTROL.matcher(raw).find()) {
            throw new IllegalArgumentException("El nombre del archivo no es seguro");
        }
        String nombre = StringUtils.cleanPath(raw).trim();
        if (nombre.isBlank() || nombre.contains("..") || nombre.contains("/") || nombre.contains("\\")
                || CONTROL.matcher(nombre).find() || !nombre.contains(".")) {
            throw new IllegalArgumentException("El nombre del archivo no es seguro");
        }
        return nombre;
    }

    private String sanearStem(String stem) {
        String ascii = Normalizer.normalize(stem, Normalizer.Form.NFKD)
                .replaceAll("\\p{M}", "");
        String saneado = ascii.replaceAll("[^A-Za-z0-9]+", "-")
                .replaceAll("^-+|-+$", "")
                .toLowerCase(Locale.ROOT);
        return saneado.isBlank() ? "documento" : saneado;
    }

    private String obtenerExtension(String filename) {
        int dot = filename.lastIndexOf('.');
        if (dot <= 0 || dot == filename.length() - 1) {
            throw new IllegalArgumentException("El archivo debe tener extensión PDF, TXT o MD");
        }
        return filename.substring(dot + 1).toLowerCase(Locale.ROOT);
    }

    private String tipoEfectivo(MultipartFile file, String extension) {
        String contentType = file.getContentType();
        return contentType == null || contentType.isBlank()
                ? EXTENSIONES_MIME.get(extension)
                : contentType;
    }

    private String extraerObjectNameDeUrl(String url) {
        if (url == null || url.isBlank()) {
            return "";
        }
        if (url.startsWith("oci://")) {
            int slash = url.indexOf('/', "oci://".length());
            return slash < 0 ? "" : url.substring(slash + 1);
        }
        String rawPath = url.contains("/o/")
                ? url.substring(url.indexOf("/o/") + 3)
                : url.substring(url.lastIndexOf('/') + 1);
        return java.net.URLDecoder.decode(rawPath, java.nio.charset.StandardCharsets.UTF_8);
    }

    private String nombreSeguroDescarga(String nombre) {
        if (nombre == null || nombre.isBlank()) {
            return "archivo";
        }
        return nombre.replaceAll("[\\r\\n\\\\/]", "_");
    }

    private void validarObjectName(String objectName) {
        if (objectName.contains("..") || objectName.contains("\\") || objectName.startsWith("/")) {
            throw new IllegalArgumentException("La ruta de almacenamiento no es segura");
        }
    }

    private void validarPaginacion(int page, int size) {
        if (page < 0) throw new IllegalArgumentException("El numero de pagina no puede ser negativo");
        if (size < 1 || size > 100) throw new IllegalArgumentException("El tamano de pagina debe estar entre 1 y 100");
    }

    private String normalizarBusqueda(String q) {
        String busqueda = q == null ? "" : q.trim();
        if (busqueda.length() > 100) throw new IllegalArgumentException("La busqueda no puede superar los 100 caracteres");
        return busqueda;
    }

    private String normalizarTipo(String tipo) {
        String alias = tipo == null ? "" : tipo.trim().toLowerCase(Locale.ROOT);
        if (alias.isEmpty()) return "";
        String mime = EXTENSIONES_MIME.get(alias);
        if (mime == null) throw new IllegalArgumentException("Tipo de archivo no permitido. Valores aceptados: pdf, txt, md");
        return mime;
    }
}
