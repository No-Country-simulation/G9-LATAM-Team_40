package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.api.dto.response.PaginaResponse;
import com.techcontent.ai.domain.service.ArchivoDownload;
import com.techcontent.ai.domain.service.ArchivoService;
import com.techcontent.ai.security.SupabaseUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.nio.charset.StandardCharsets;
import java.util.UUID;

@RestController
@RequestMapping("/api/archivos")
@RequiredArgsConstructor
public class ArchivoController {

    private final ArchivoService archivoService;

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ArchivoResponse> subir(
            @RequestParam("file") MultipartFile file,
            @RequestParam("dominio") String dominio,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(archivoService.subir(file, userDetails.getUserId(), dominio));
    }

    @GetMapping
    public ResponseEntity<PaginaResponse<ArchivoResponse>> listar(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "") String q,
            @RequestParam(defaultValue = "") String tipo,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(archivoService.listar(userDetails.getUserId(), page, size, q, tipo));
    }

    @GetMapping("/{id}/descarga")
    public ResponseEntity<InputStreamResource> descargar(
            @PathVariable UUID id,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        ArchivoDownload download = archivoService.descargar(id, userDetails.getUserId());
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.parseMediaType(download.tipo()));
        headers.setContentLength(download.tamano());
        headers.setContentDisposition(ContentDisposition.attachment()
                .filename(download.nombre(), StandardCharsets.UTF_8)
                .build());
        return new ResponseEntity<>(new InputStreamResource(download.contenido()), headers, HttpStatus.OK);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ArchivoResponse> obtener(
            @PathVariable UUID id,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(archivoService.obtenerPorId(id, userDetails.getUserId()));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> eliminar(
            @PathVariable UUID id,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        archivoService.eliminar(id, userDetails.getUserId());
        return ResponseEntity.accepted().build();
    }
}
