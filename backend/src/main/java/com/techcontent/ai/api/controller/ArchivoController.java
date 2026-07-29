package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.domain.service.ArchivoService;
import com.techcontent.ai.security.SupabaseUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/archivos")
@RequiredArgsConstructor
public class ArchivoController {

    private final ArchivoService archivoService;

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ArchivoResponse> subir(
            @RequestParam("file") MultipartFile file,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(archivoService.subir(file, userDetails.getUserId()));
    }

    @GetMapping
    public ResponseEntity<List<ArchivoResponse>> listar(
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(archivoService.listar(userDetails.getUserId()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ArchivoResponse> obtener(
            @PathVariable UUID id,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(archivoService.obtenerPorId(id, userDetails.getUserId()));
    }
}
