package com.techcontent.ai.api.dto.request;

import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

@Getter
@Setter
public class ArchivoFiltroDTO {

    private static final Map<String, String> TIPOS_FILTRO = Map.of(
            "pdf", "application/pdf",
            "txt", "text/plain",
            "md", "text/markdown",
            "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    );

    @Size(max = 100, message = "El nombre de búsqueda no puede superar los 100 caracteres")
    private String nombre;

    @Size(max = 20, message = "El tipo de archivo no es válido")
    private String tipo;

    private UUID userId;

    private LocalDateTime fechaInicio;

    private LocalDateTime fechaFin;

    // Compatible con el parámetro tradicional 'q' de las pruebas
    public void setQ(String q) {
        this.nombre = (q != null && !q.trim().isEmpty()) ? q.trim() : null;
    }

    public void setNombre(String nombre) {
        this.nombre = (nombre != null && !nombre.trim().isEmpty()) ? nombre.trim() : null;
    }

    public void setTipo(String tipo) {
        if (tipo == null || tipo.trim().isEmpty()) {
            this.tipo = null;
            return;
        }
        String alias = tipo.trim().toLowerCase(Locale.ROOT);
        // Traduce automáticamente 'pdf' a 'application/pdf', etc.
        String tipoMime = TIPOS_FILTRO.get(alias);
        this.tipo = (tipoMime != null) ? tipoMime : alias;
    }
}