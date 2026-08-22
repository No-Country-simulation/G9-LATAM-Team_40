package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.GrafoResponse;
import com.techcontent.ai.domain.service.GrafoService;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

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
    public ResponseEntity<List<GrafoResponse>> obtenerHistorial() {
        return ResponseEntity.ok(grafoService.obtenerHistorial());
    }

    @GetMapping("/buscar")
    public ResponseEntity<List<GrafoResponse>> buscarPorFechas(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime desde,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime hasta) {
        return ResponseEntity.ok(grafoService.buscarPorRangoFechas(desde, hasta));
    }
}