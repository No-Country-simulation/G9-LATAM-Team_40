package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.request.ConsultaRequest;
import com.techcontent.ai.api.dto.response.ConsultaResponse;
import com.techcontent.ai.domain.service.ConsultaService;
import com.techcontent.ai.security.SupabaseUserDetails;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

import java.util.List;

@RestController
@RequestMapping("/api/consultas")
@RequiredArgsConstructor
public class ConsultaController {

    private final ConsultaService consultaService;

    @PostMapping
    public ResponseEntity<ConsultaResponse> analizar(
            @Valid @RequestBody ConsultaRequest request,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(consultaService.analizar(request, userDetails.getUserId()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ConsultaResponse> obtenerPorId(
            @PathVariable UUID id,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(consultaService.obtenerPorId(id, userDetails.getUserId()));
    }

    @GetMapping("/buscar")
    public ResponseEntity<List<ConsultaResponse>> buscar(
            @RequestParam String q,
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(consultaService.buscar(q, userDetails.getUserId()));
    }

    @GetMapping
    public ResponseEntity<List<ConsultaResponse>> listar(
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(consultaService.listarPorUsuario(userDetails.getUserId()));
    }
}
