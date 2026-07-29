package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.request.ContenidoLoteRequest;
import com.techcontent.ai.api.dto.request.ContenidoRequest;
import com.techcontent.ai.api.dto.response.ContenidoResponse;
import com.techcontent.ai.domain.service.ContenidoService;
import com.techcontent.ai.security.SupabaseUserDetails;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/contenido")
@RequiredArgsConstructor
public class ContenidoController {

    private final ContenidoService contenidoService;

    @PostMapping
    public ResponseEntity<ContenidoResponse> clasificar(
            @Valid @RequestBody ContenidoRequest request,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(contenidoService.clasificar(request, userDetails.getUserId()));
    }

    @PostMapping("/lote")
    public ResponseEntity<List<ContenidoResponse>> clasificarLote(
            @Valid @RequestBody ContenidoLoteRequest request,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(contenidoService.procesarLote(request, userDetails.getUserId()));
    }

    @GetMapping("/buscar")
    public ResponseEntity<List<ContenidoResponse>> buscar(
            @RequestParam String q,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(contenidoService.buscar(q, userDetails.getUserId()));
    }

    @GetMapping
    public ResponseEntity<List<ContenidoResponse>> listar(
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(contenidoService.listarPorUsuario(userDetails.getUserId()));
    }
}
