package com.techcontent.ai.api;

import com.techcontent.ai.dto.ContenidoRequest;
import com.techcontent.ai.dto.ContenidoResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/contenidos")
public class ContenidoController {

    @PostMapping
    public ResponseEntity<ContenidoResponse> crearContenido(@Valid @RequestBody ContenidoRequest request) {
        // Simulación de respuesta exitosa para validar el flujo REST y Bean Validation
        ContenidoResponse response = new ContenidoResponse(
            1L,
            request.titulo(),
            request.texto(),
            "Usuario QA",
            LocalDateTime.now()
        );
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping
    public ResponseEntity<List<ContenidoResponse>> listarContenidos() {
        List<ContenidoResponse> lista = List.of(
            new ContenidoResponse(1L, "Introducción a Spring Boot", "Contenido de prueba para la API REST del equipo 4.", "Usuario QA", LocalDateTime.now())
        );
        return ResponseEntity.ok(lista);
    }
}