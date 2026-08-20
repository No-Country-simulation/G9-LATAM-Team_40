package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.service.CategoriaService;
import com.techcontent.ai.security.SupabaseUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/categorias")
@RequiredArgsConstructor
public class CategoriaController {

    private final CategoriaService categoriaService;

    @GetMapping
    public ResponseEntity<List<CategoriaResponse>> listar(
            @AuthenticationPrincipal SupabaseUserDetails userDetails) {
        return ResponseEntity.ok(categoriaService.listarConConteo(userDetails.getUserId()));
    }
}