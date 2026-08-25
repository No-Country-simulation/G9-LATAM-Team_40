package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.exception.ContenidoNotFoundException;
import com.techcontent.ai.api.dto.request.ConsultaRequest;
import com.techcontent.ai.api.dto.response.ConsultaResponse;
import com.techcontent.ai.api.dto.response.TrazabilidadSeccionResponse;
import com.techcontent.ai.domain.model.Contenido;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.ml.QueryResponse;
import com.techcontent.ai.integration.ml.TrazabilidadSeccionDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class ConsultaService {

    private static final String CATEGORIA_POR_DEFECTO = "Sin Categoría";

    private final ContenidoRepository repository;
    private final MlClient mlClient;
    private final ObjectMapper objectMapper;

    @Transactional
    public ConsultaResponse analizar(ConsultaRequest request, UUID userId) {
        QueryResponse queryResponse = mlClient.queryGraphRag(request.pregunta(), userId);
        List<TrazabilidadSeccionResponse> trazabilidad = mapTrace(queryResponse);
        TrazabilidadSeccionResponse fuentePrincipal = trazabilidad.stream().findFirst().orElse(null);

        String categoria = fuentePrincipal != null && fuentePrincipal.categoria() != null
                && !fuentePrincipal.categoria().isBlank()
                ? fuentePrincipal.categoria()
                : CATEGORIA_POR_DEFECTO;
        Double relevancia = fuentePrincipal != null && fuentePrincipal.relevancia() != null
                ? fuentePrincipal.relevancia()
                : 0.0;
        List<String> palabrasClave = fuentePrincipal != null && fuentePrincipal.palabrasClave() != null
                ? fuentePrincipal.palabrasClave()
                : List.of();
        LocalDateTime procesadoEn = LocalDateTime.now();

        Contenido contenido = Contenido.builder()
                .userId(userId)
                .titulo(tituloDerivado(request.pregunta()))
                .texto(request.pregunta())
                .categoria(categoria)
                .relevancia(relevancia)
                .palabrasClave(palabrasClave)
                .trazabilidadJson(serializarTrazabilidad(trazabilidad))
                .tiempoSegundos(queryResponse != null ? queryResponse.tiempoSegundos() : null)
                .respuesta(queryResponse != null ? queryResponse.respuesta() : "")
                .procesadoEn(procesadoEn)
                .build();

        return toResponse(repository.save(contenido));
    }

    @Transactional(readOnly = true)
    public ConsultaResponse obtenerPorId(UUID id, UUID userId) {
        return repository.findByIdAndUserId(id, userId)
                .map(this::toResponse)
                .orElseThrow(() -> new ContenidoNotFoundException(id));
    }

    public List<ConsultaResponse> buscar(String query, UUID userId) {
        return repository.buscarPorKeyword(query, userId).stream()
                .map(this::toResponse)
                .toList();
    }

    public List<ConsultaResponse> listarPorUsuario(UUID userId) {
        return repository.findByUserId(userId).stream()
                .map(this::toResponse)
                .toList();
    }

    private List<TrazabilidadSeccionResponse> mapTrace(QueryResponse queryResponse) {
        if (queryResponse == null || queryResponse.trazabilidad() == null) {
            return List.of();
        }
        return queryResponse.trazabilidad().stream()
                .map(this::mapTrace)
                .toList();
    }

    private TrazabilidadSeccionResponse mapTrace(TrazabilidadSeccionDto trace) {
        if (trace == null) {
            return null;
        }
        return new TrazabilidadSeccionResponse(
                trace.documentoId(),
                trace.documentoTitulo(),
                trace.categoria(),
                trace.palabrasClave() == null ? List.of() : trace.palabrasClave(),
                trace.tituloSeccion(),
                trace.rutaJerarquica() == null ? List.of() : trace.rutaJerarquica(),
                trace.nivel(),
                trace.dominio(),
                trace.score(),
                trace.corpus(),
                trace.archivoId()
        );
    }

    private String serializarTrazabilidad(List<TrazabilidadSeccionResponse> trazabilidad) {
        try {
            return objectMapper.writeValueAsString(trazabilidad);
        } catch (JsonProcessingException e) {
            log.error("No se pudo serializar la trazabilidad de la consulta", e);
            return "[]";
        }
    }

    private List<TrazabilidadSeccionResponse> deserializarTrazabilidad(String json) {
        if (json == null || json.isBlank()) {
            return List.of();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<>() {});
        } catch (JsonProcessingException | RuntimeException e) {
            log.warn("Trazabilidad persistida malformada; se devuelve lista vacía", e);
            return List.of();
        }
    }

    private ConsultaResponse toResponse(Contenido contenido) {
        return new ConsultaResponse(
                contenido.getId() == null ? null : contenido.getId().toString(),
                contenido.getTexto(),
                contenido.getRespuesta(),
                contenido.getCategoria() == null ? CATEGORIA_POR_DEFECTO : contenido.getCategoria(),
                contenido.getRelevancia() == null ? 0.0 : contenido.getRelevancia(),
                contenido.getPalabrasClave() == null ? List.of() : contenido.getPalabrasClave(),
                deserializarTrazabilidad(contenido.getTrazabilidadJson()),
                contenido.getTiempoSegundos(),
                contenido.getProcesadoEn()
        );
    }

    private String tituloDerivado(String pregunta) {
        String limpio = pregunta == null ? "" : pregunta.trim();
        return limpio.length() <= 120 ? limpio : limpio.substring(0, 120);
    }
}
