package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.request.ContenidoLoteRequest;
import com.techcontent.ai.api.dto.request.ContenidoRequest;
import com.techcontent.ai.api.dto.response.ContenidoResponse;
import com.techcontent.ai.domain.model.Contenido;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.ml.QueryResponse;
import com.techcontent.ai.integration.ml.TrazabilidadSeccionDto;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ContenidoServiceTest {

    @Mock
    private ContenidoRepository repository;

    @Mock
    private MlClient mlClient;

    @Mock
    private ObjectMapper objectMapper;

    @InjectMocks
    private ContenidoService service;

    private static final UUID USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");

    private Contenido contenidoGuardado(UUID id, String categoria, Double probabilidad, List<String> keywords) {
        return Contenido.builder()
                .id(id)
                .userId(USER_ID)
                .titulo("Titulo test")
                .texto("Texto de prueba")
                .categoria(categoria)
                .probabilidad(probabilidad)
                .palabrasClave(keywords)
                .respuesta("Respuesta de prueba del LLM")
                .grafoData("[]")
                .procesadoEn(LocalDateTime.now())
                .build();
    }

    private QueryResponse crearQueryResponseSimulado(String categoria, Double score, List<String> keywords) {
        TrazabilidadSeccionDto trazabilidad = new TrazabilidadSeccionDto(
                "doc1", "Titulo Doc", categoria, keywords,
                "Seccion 1", List.of("Cap 1"), 1, "Dominio", score, "/path/doc.pdf"
        );
        return new QueryResponse("Pregunta test", "Respuesta de prueba del LLM", List.of(trazabilidad), 1.0);
    }

    @Test
    void clasificar_deberiaLlamarAlMlYPersistirElContenido() throws JsonProcessingException {
        ContenidoRequest request = new ContenidoRequest("Titulo", "Texto de prueba para clasificar");
        QueryResponse queryResponse = crearQueryResponseSimulado("Backend", 0.93, List.of("Java", "Spring"));
        UUID savedId = UUID.randomUUID();

        when(mlClient.queryGraphRag(request.texto())).thenReturn(queryResponse);
        when(objectMapper.writeValueAsString(any())).thenReturn("[]");
        when(repository.save(any(Contenido.class))).thenReturn(contenidoGuardado(savedId, "Backend", 0.93, List.of("Java", "Spring")));

        ContenidoResponse response = service.clasificar(request, USER_ID);

        assertThat(response.categoria()).isEqualTo("Backend");
        assertThat(response.probabilidad()).isEqualTo(0.93);
        assertThat(response.palabrasClave()).containsExactly("Java", "Spring");
        assertThat(response.respuesta()).isEqualTo("Respuesta de prueba del LLM");

        verify(mlClient, times(1)).queryGraphRag(request.texto());
        verify(repository, times(1)).save(any(Contenido.class));
    }

    @Test
    void procesarLote_deberiaClasificarCadaItemDelLote() throws JsonProcessingException {
        ContenidoRequest item1 = new ContenidoRequest("Titulo 1", "Texto numero uno para clasificar");
        ContenidoRequest item2 = new ContenidoRequest("Titulo 2", "Texto numero dos para clasificar");
        ContenidoLoteRequest loteRequest = new ContenidoLoteRequest(List.of(item1, item2));

        QueryResponse queryResponse = crearQueryResponseSimulado("Frontend", 0.88, List.of("React", "TypeScript"));

        when(mlClient.queryGraphRag(any())).thenReturn(queryResponse);
        when(objectMapper.writeValueAsString(any())).thenReturn("[]");
        when(repository.save(any(Contenido.class))).thenAnswer(inv -> {
            Contenido c = inv.getArgument(0);
            return Contenido.builder()
                    .id(UUID.randomUUID())
                    .userId(USER_ID)
                    .titulo(c.getTitulo())
                    .texto(c.getTexto())
                    .categoria(c.getCategoria())
                    .probabilidad(c.getProbabilidad())
                    .palabrasClave(c.getPalabrasClave())
                    .respuesta(c.getRespuesta())
                    .grafoData(c.getGrafoData())
                    .procesadoEn(c.getProcesadoEn())
                    .build();
        });

        List<ContenidoResponse> responses = service.procesarLote(loteRequest, USER_ID);

        assertThat(responses).hasSize(2);
        assertThat(responses).allMatch(r -> r.categoria().equals("Frontend"));
        verify(mlClient, times(2)).queryGraphRag(any());
        verify(repository, times(2)).save(any(Contenido.class));
    }

    @Test
    void buscar_deberiaRetornarResultadosDeLaQuery() {
        UUID id = UUID.randomUUID();
        when(repository.buscarPorKeyword("java", USER_ID)).thenReturn(
                List.of(contenidoGuardado(id, "Backend", 0.90, List.of("java")))
        );

        List<ContenidoResponse> responses = service.buscar("java", USER_ID);

        assertThat(responses).hasSize(1);
        assertThat(responses.get(0).palabrasClave()).contains("java");
        verify(repository).buscarPorKeyword("java", USER_ID);
    }

    @Test
    void listarPorUsuario_deberiaRetornarTodosLosContenidosDelUsuario() {
        when(repository.findByUserId(USER_ID)).thenReturn(
                List.of(
                        contenidoGuardado(UUID.randomUUID(), "Backend", 0.91, List.of("Java")),
                        contenidoGuardado(UUID.randomUUID(), "DevOps", 0.85, List.of("Docker"))
                )
        );

        List<ContenidoResponse> responses = service.listarPorUsuario(USER_ID);

        assertThat(responses).hasSize(2);
        verify(repository).findByUserId(USER_ID);
    }
}