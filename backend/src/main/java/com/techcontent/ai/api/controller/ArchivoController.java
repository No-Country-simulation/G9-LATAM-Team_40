package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.api.dto.response.PaginaResponse;
import com.techcontent.ai.domain.service.ArchivoService;
import com.techcontent.ai.security.SupabaseUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.UUID;

@RestController
@RequestMapping("/api/archivos")
@RequiredArgsConstructor
public class ArchivoController {

    private final ArchivoService archivoService;

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ArchivoResponse> subir(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "categoria", required = false) String categoria,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {

        ArchivoResponse response = archivoService.subir(file, userDetails.getUserId(), categoria);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
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
        return ResponseEntity.noContent().build();
    }
}