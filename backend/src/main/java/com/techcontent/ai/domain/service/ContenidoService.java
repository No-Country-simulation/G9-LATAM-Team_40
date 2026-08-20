package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.request.ContenidoLoteRequest;
import com.techcontent.ai.api.dto.request.ContenidoRequest;
import com.techcontent.ai.api.dto.response.ContenidoResponse;
import com.techcontent.ai.api.dto.response.ContenidoRelacionadoResponse;
import com.techcontent.ai.domain.model.Contenido;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.ml.QueryResponse;
import com.techcontent.ai.integration.ml.TrazabilidadSeccionDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ContenidoService {

    private final ContenidoRepository repository;
    private final MlClient mlClient;
    private final ObjectMapper objectMapper;

    public ContenidoResponse clasificar(ContenidoRequest request, UUID userId) {
        QueryResponse queryResponse = mlClient.queryGraphRag(request.texto());
        TrazabilidadSeccionDto fuentePrincipal = queryResponse.trazabilidad().stream()
                .findFirst()
                .orElse(null);

        String categoria = (fuentePrincipal != null && fuentePrincipal.categoria() != null)
                ? fuentePrincipal.categoria() : "Sin Categoría";

        Double score = fuentePrincipal != null ? fuentePrincipal.score() : 0.0;
        List<String> palabrasClave = fuentePrincipal != null ? fuentePrincipal.palabrasClave() : List.of();
        String trazabilidadJson = "";
        try {
            trazabilidadJson = objectMapper.writeValueAsString(queryResponse.trazabilidad());
        } catch (JsonProcessingException e) {
            trazabilidadJson = "[]";
        }

        Contenido contenido = Contenido.builder()
                .userId(userId)
                .titulo(request.titulo())
                .texto(request.texto())
                .categoria(categoria)
                .probabilidad(score)
                .palabrasClave(palabrasClave)
                .respuesta(queryResponse.respuesta())
                .grafoData(trazabilidadJson)
                .procesadoEn(LocalDateTime.now())
                .build();

        Contenido saved = repository.save(contenido);
        return toResponse(saved);
    }

    @Transactional
    public List<ContenidoResponse> procesarLote(ContenidoLoteRequest request, UUID userId) {
        return request.contenidos().stream()
                .map(item -> clasificar(item, userId))
                .toList();
    }

    public List<ContenidoResponse> buscar(String query, UUID userId) {
        return repository.buscarPorKeyword(query, userId).stream()
                .map(this::toResponse)
                .toList();
    }

    public List<ContenidoResponse> listarPorUsuario(UUID userId) {
        return repository.findByUserId(userId).stream()
                .map(this::toResponse)
                .toList();
    }

    private ContenidoResponse toResponse(Contenido contenido) {
        List<ContenidoRelacionadoResponse> relacionados = List.of();

        Object grafoDataParsed;
        if (contenido.getGrafoData() != null && !contenido.getGrafoData().isBlank()) {
            try {
                grafoDataParsed = objectMapper.readValue(
                        contenido.getGrafoData(),
                        new com.fasterxml.jackson.core.type.TypeReference<List<TrazabilidadSeccionDto>>() {}
                );
            } catch (JsonProcessingException e) {
                grafoDataParsed = List.of();
            }
        } else {
            grafoDataParsed = List.of();
        }

        return new ContenidoResponse(
                contenido.getId().toString(),
                contenido.getCategoria(),
                contenido.getProbabilidad(),
                contenido.getPalabrasClave(),
                relacionados,
                contenido.getRespuesta(),
                grafoDataParsed,
                contenido.getProcesadoEn()
        );
    }
}