package com.techcontent.ai.domain.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "contenidos")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Contenido {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(nullable = false)
    private String titulo;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String texto;

    private String categoria;

    private Double probabilidad;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(
            name = "contenido_palabras_clave",
            joinColumns = @JoinColumn(name = "contenido_id")
    )
    @Column(name = "palabra")
    @Builder.Default
    private List<String> palabrasClave = new ArrayList<>();

    @Column(name = "procesado_en")
    private LocalDateTime procesadoEn;
}
