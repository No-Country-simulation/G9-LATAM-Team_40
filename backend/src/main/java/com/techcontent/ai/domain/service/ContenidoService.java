package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.request.ContenidoLoteRequest;
import com.techcontent.ai.api.dto.request.ContenidoRequest;
import com.techcontent.ai.api.dto.response.ContenidoResponse;
import com.techcontent.ai.api.dto.response.ContenidoRelacionadoResponse;
import com.techcontent.ai.api.exception.ContenidoNotFoundException;
import com.techcontent.ai.domain.model.Contenido;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import com.techcontent.ai.integration.ml.MLClient;
import com.techcontent.ai.dto.MlResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ContenidoService {

    private final ContenidoRepository repository;
    private final MLClient mlClient;

    public ContenidoResponse clasificar(ContenidoRequest request, UUID userId) {
        MlResponse mlResponse = mlClient.predict(request.texto());

        Contenido contenido = Contenido.builder()
                .userId(userId)
                .titulo(request.titulo())
                .texto(request.texto())
                .categoria(mlResponse.categoria())
                .probabilidad(mlResponse.probabilidad())
                .palabrasClave(mlResponse.palabrasClave())
                .procesadoEn(LocalDateTime.now())
                .build();

        Contenido saved = repository.save(contenido);
        return toResponse(saved);
    }

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

        return new ContenidoResponse(
                contenido.getId().toString(),
                contenido.getCategoria(),
                contenido.getProbabilidad(),
                contenido.getPalabrasClave(),
                relacionados,
                contenido.getProcesadoEn()
        );
    }
}