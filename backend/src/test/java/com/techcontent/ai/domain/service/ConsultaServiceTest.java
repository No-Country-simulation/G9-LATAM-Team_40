package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.request.ConsultaRequest;
import com.techcontent.ai.api.dto.response.ConsultaResponse;
import com.techcontent.ai.domain.model.Contenido;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.ml.QueryResponse;
import com.techcontent.ai.integration.ml.TrazabilidadSeccionDto;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ConsultaServiceTest {

    @Mock private ContenidoRepository repository;
    @Mock private MlClient mlClient;
    private ConsultaService service;

    private static final UUID USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");

    @BeforeEach
    void setUp() {
        service = new ConsultaService(repository, mlClient, new ObjectMapper());
    }

    @Test
    void analizar_mapeaScoreAPublicaRelevanciaYPersistetrazabilidad() {
        ConsultaRequest request = new ConsultaRequest("¿Qué obligaciones de seguridad contiene el corpus?");
        TrazabilidadSeccionDto trace = new TrazabilidadSeccionDto(
                "doc-1", "Manual de seguridad", "Seguridad", List.of("riesgo"),
                "Obligaciones", List.of("Capítulo 1"), 1, "ISOs", 0.93, "BASE", null
        );
        when(mlClient.queryGraphRag(request.pregunta(), USER_ID))
                .thenReturn(new QueryResponse(request.pregunta(), "Respuesta", List.of(trace), 1.25));
        when(repository.save(any(Contenido.class))).thenAnswer(invocation -> {
            Contenido value = invocation.getArgument(0);
            value.setId(UUID.randomUUID());
            return value;
        });

        ConsultaResponse response = service.analizar(request, USER_ID);

        assertThat(response.relevancia()).isEqualTo(0.93);
        assertThat(response.trazabilidad()).singleElement().satisfies(item -> {
            assertThat(item.relevancia()).isEqualTo(0.93);
            assertThat(item.corpus()).isEqualTo("BASE");
        });
        assertThat(response.tiempoSegundos()).isEqualTo(1.25);
        verify(mlClient).queryGraphRag(request.pregunta(), USER_ID);
        verify(repository).save(any(Contenido.class));
    }

    @Test
    void toResponse_jsonMalformado_devuelveTrazabilidadVacia() {
        Contenido legacy = Contenido.builder()
                .id(UUID.randomUUID())
                .userId(USER_ID)
                .titulo("Pregunta antigua")
                .texto("Pregunta antigua")
                .categoria("Sin Categoría")
                .relevancia(0.0)
                .palabrasClave(List.of())
                .trazabilidadJson("{")
                .respuesta("Respuesta")
                .procesadoEn(LocalDateTime.now())
                .build();
        when(repository.findByUserId(USER_ID)).thenReturn(List.of(legacy));

        List<ConsultaResponse> response = service.listarPorUsuario(USER_ID);

        assertThat(response).singleElement().satisfies(item -> assertThat(item.trazabilidad()).isEmpty());
    }
}
