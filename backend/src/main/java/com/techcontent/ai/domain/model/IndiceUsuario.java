package com.techcontent.ai.domain.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
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
@Table(name = "indices_usuario")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class IndiceUsuario {

    @Id
    @Column(name = "user_id")
    private UUID userId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private IndiceEstado estado = IndiceEstado.IDLE;

    private String etapa;

    @Column(columnDefinition = "TEXT")
    private String mensaje;

    @Column(name = "ml_job_id")
    private UUID mlJobId;

    @Column(name = "release_id")
    private String releaseId;

    @Column(name = "requested_generation", nullable = false)
    @Builder.Default
    private long requestedGeneration = 0L;

    @Column(name = "running_generation")
    private Long runningGeneration;

    @Column(name = "rebuild_pendiente", nullable = false)
    @Builder.Default
    private boolean rebuildPendiente = false;

    @Column(name = "documentos_json", columnDefinition = "TEXT")
    private String documentosJson;

    @Column(name = "creado_en")
    private LocalDateTime creadoEn;

    @Column(name = "actualizado_en")
    private LocalDateTime actualizadoEn;

    @Column(name = "iniciado_en")
    private LocalDateTime iniciadoEn;

    @Column(name = "finalizado_en")
    private LocalDateTime finalizadoEn;
}
