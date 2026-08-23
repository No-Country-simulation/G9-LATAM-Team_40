package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.GrafoResponse;
import com.techcontent.ai.domain.service.GrafoService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/grafos")
@RequiredArgsConstructor
public class GrafoController {

    private final GrafoService grafoService;

    @PostMapping("/sincronizar")
    public ResponseEntity<GrafoResponse> sincronizar(
            @RequestParam(required = false) String objectName
    ) {
        GrafoResponse response = grafoService.sincronizarDesdeOci(objectName);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/actual")
    public ResponseEntity<GrafoResponse> obtenerUltimo() {
        return ResponseEntity.ok(grafoService.obtenerUltimo());
    }

    @GetMapping("/historial")
    public ResponseEntity<Page<GrafoResponse>> obtenerHistorial(
            @PageableDefault(size = 10) Pageable pageable
    ) {
        return ResponseEntity.ok(grafoService.obtenerHistorial(pageable));
    }

    @GetMapping("/buscarfecha")
    public ResponseEntity<List<GrafoResponse>> buscarPorFechas(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate desde,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate hasta) {
        return ResponseEntity.ok(grafoService.buscarPorRangoFechas(desde, hasta));
    }

    @GetMapping("/id/{id}")
    public ResponseEntity<GrafoResponse> obtenerPorId(@PathVariable UUID id) {
        return ResponseEntity.ok(grafoService.obtenerPorId(id));
    }
}