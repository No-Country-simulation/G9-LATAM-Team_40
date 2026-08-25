package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.request.ConsultaRequest;
import com.techcontent.ai.api.dto.response.ConsultaResponse;
import com.techcontent.ai.domain.model.Contenido;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.ml.QueryResponse;
import com.techcontent.ai.integration.ml.TrazabilidadSeccionDto;
import com.techcontent.ai.api.exception.ContenidoNotFoundException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
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

    @Test
    void obtenerPorId_usuarioPropietario_reconstruyeRespuestaPersistidaSinMl() {
        UUID queryId = UUID.fromString("00000000-0000-0000-0000-000000000010");
        LocalDateTime procesadoEn = LocalDateTime.of(2026, 8, 24, 10, 0);
        Contenido persisted = Contenido.builder()
                .id(queryId)
                .userId(USER_ID)
                .texto("Pregunta persistida")
                .respuesta("Respuesta persistida")
                .categoria("Seguridad")
                .relevancia(0.93)
                .palabrasClave(List.of("riesgo"))
                .trazabilidadJson("""
                        [{"documento_id":"doc-1","documento_titulo":"Manual","categoria":"Seguridad","palabras_clave":["riesgo"],"titulo_seccion":"Obligaciones","ruta_jerarquica":["Capítulo 1"],"nivel":1,"dominio":"ISOs","relevancia":0.93,"corpus":"BASE","archivo_id":null}]
                        """)
                .tiempoSegundos(1.25)
                .procesadoEn(procesadoEn)
                .build();
        when(repository.findByIdAndUserId(queryId, USER_ID)).thenReturn(java.util.Optional.of(persisted));

        ConsultaResponse response = service.obtenerPorId(queryId, USER_ID);

        assertThat(response.id()).isEqualTo(queryId.toString());
        assertThat(response.pregunta()).isEqualTo("Pregunta persistida");
        assertThat(response.respuesta()).isEqualTo("Respuesta persistida");
        assertThat(response.categoriaFuentePrincipal()).isEqualTo("Seguridad");
        assertThat(response.relevancia()).isEqualTo(0.93);
        assertThat(response.palabrasClave()).containsExactly("riesgo");
        assertThat(response.tiempoSegundos()).isEqualTo(1.25);
        assertThat(response.procesadoEn()).isEqualTo(procesadoEn);
        assertThat(response.trazabilidad()).singleElement().satisfies(trace -> {
            assertThat(trace.documentoId()).isEqualTo("doc-1");
            assertThat(trace.tituloSeccion()).isEqualTo("Obligaciones");
            assertThat(trace.corpus()).isEqualTo("BASE");
        });
        verify(repository).findByIdAndUserId(queryId, USER_ID);
        verifyNoInteractions(mlClient);
    }

    @Test
    void obtenerPorId_usuarioAjeno_lanzaContenidoNotFoundSinConsultarMl() {
        UUID queryId = UUID.fromString("00000000-0000-0000-0000-000000000011");
        when(repository.findByIdAndUserId(queryId, USER_ID)).thenReturn(java.util.Optional.empty());

        assertThatThrownBy(() -> service.obtenerPorId(queryId, USER_ID))
                .isInstanceOf(ContenidoNotFoundException.class);

        verify(repository).findByIdAndUserId(queryId, USER_ID);
        verifyNoInteractions(mlClient);
    }
}
