package com.techcontent.ai.domain.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "grafos")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Grafo {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "json_data", columnDefinition = "TEXT", nullable = false)
    private String jsonData;

    @Column(name = "fecha_creacion")
    private LocalDateTime fechaCreacion;
}