package com.techcontent.ai.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "archivos")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Archivo {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(nullable = false)
    private String nombre;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String url;

    @Column(name = "documento_id")
    private String documentoId;

    private String dominio;

    @Column(name = "object_name")
    private String objectName;

    private Long tamano;

    private String tipo;

    @Column(name = "subido_en")
    private LocalDateTime subidoEn;

    @Column(name = "indexado_en")
    private LocalDateTime indexadoEn;

    @Column(name = "pendiente_eliminacion", nullable = false)
    @Builder.Default
    private boolean pendienteEliminacion = false;
}
