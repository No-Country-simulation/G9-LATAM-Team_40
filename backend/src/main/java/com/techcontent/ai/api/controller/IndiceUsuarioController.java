package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.IndiceResponse;
import com.techcontent.ai.domain.service.IndiceUsuarioService;
import com.techcontent.ai.security.SupabaseUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/indice")
@RequiredArgsConstructor
public class IndiceUsuarioController {

    private final IndiceUsuarioService indiceUsuarioService;

    @GetMapping
    public ResponseEntity<IndiceResponse> estado(
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(indiceUsuarioService.estado(userDetails.getUserId()));
    }

    @PostMapping("/reintentar")
    public ResponseEntity<IndiceResponse> reintentar(
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.status(HttpStatus.ACCEPTED)
                .body(indiceUsuarioService.reintentar(userDetails.getUserId()));
    }
}
