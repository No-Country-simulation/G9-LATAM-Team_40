package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.ConsultaResponse;
import com.techcontent.ai.api.dto.response.TrazabilidadSeccionResponse;
import com.techcontent.ai.api.exception.ContenidoNotFoundException;
import com.techcontent.ai.domain.service.ConsultaService;
import com.techcontent.ai.security.JwtService;
import com.techcontent.ai.security.SupabaseUserDetails;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.http.MediaType.APPLICATION_JSON;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ConsultaController.class)
@AutoConfigureMockMvc(addFilters = false)
class ConsultaControllerIntegrationTest {

    @Autowired private MockMvc mockMvc;
    @MockBean private ConsultaService consultaService;
    @MockBean private JwtService jwtService;

    private static final UUID USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");

    @Test
    void post_consulta_exponeRelevanciaYScoreMapeado() throws Exception {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                new SupabaseUserDetails(USER_ID, "user@example.com", "authenticated"), null));
        ConsultaResponse response = new ConsultaResponse(
                UUID.randomUUID().toString(),
                "¿Qué obligaciones de seguridad contiene el corpus?",
                "Respuesta",
                "Seguridad",
                0.92,
                List.of("riesgo"),
                List.of(new TrazabilidadSeccionResponse("doc", "Manual", "Seguridad", List.of("riesgo"), "Obligaciones", List.of("Capítulo 1"), 1, "ISOs", 0.92, "BASE", null)),
                1.1,
                null
        );
        when(consultaService.analizar(any(), eq(USER_ID))).thenReturn(response);

        mockMvc.perform(post("/api/consultas")
                        .contentType(APPLICATION_JSON)
                        .content("{\"pregunta\":\"¿Qué obligaciones de seguridad contiene el corpus?\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.relevancia").value(0.92))
                .andExpect(jsonPath("$.trazabilidad[0].relevancia").value(0.92))
                .andExpect(jsonPath("$.trazabilidad[0].corpus").value("BASE"));
    }

    @Test
    void get_consulta_autenticada_exponeCamposPersistidosCompletos() throws Exception {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                new SupabaseUserDetails(USER_ID, "user@example.com", "authenticated"), null));
        UUID queryId = UUID.fromString("00000000-0000-0000-0000-000000000010");
        ConsultaResponse response = new ConsultaResponse(
                queryId.toString(),
                "Pregunta persistida",
                "Respuesta persistida",
                "Seguridad",
                0.93,
                List.of("riesgo"),
                List.of(new TrazabilidadSeccionResponse(
                        "doc-1", "Manual", "Seguridad", List.of("riesgo"), "Obligaciones",
                        List.of("Capítulo 1"), 1, "ISOs", 0.93, "BASE", UUID.fromString("00000000-0000-0000-0000-000000000020")
                )),
                1.25,
                LocalDateTime.of(2026, 8, 24, 10, 0)
        );
        when(consultaService.obtenerPorId(queryId, USER_ID)).thenReturn(response);

        mockMvc.perform(get("/api/consultas/{id}", queryId))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(queryId.toString()))
                .andExpect(jsonPath("$.pregunta").value("Pregunta persistida"))
                .andExpect(jsonPath("$.respuesta").value("Respuesta persistida"))
                .andExpect(jsonPath("$.categoria_fuente_principal").value("Seguridad"))
                .andExpect(jsonPath("$.relevancia").value(0.93))
                .andExpect(jsonPath("$.palabras_clave[0]").value("riesgo"))
                .andExpect(jsonPath("$.trazabilidad[0].documento_id").value("doc-1"))
                .andExpect(jsonPath("$.trazabilidad[0].archivo_id").value("00000000-0000-0000-0000-000000000020"))
                .andExpect(jsonPath("$.tiempo_segundos").value(1.25))
                .andExpect(jsonPath("$.procesado_en").value("2026-08-24T10:00:00"));
    }

    @Test
    void get_consulta_noEncontrada_devuelve404SinRevelarPropietario() throws Exception {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                new SupabaseUserDetails(USER_ID, "user@example.com", "authenticated"), null));
        UUID queryId = UUID.fromString("00000000-0000-0000-0000-000000000011");
        when(consultaService.obtenerPorId(queryId, USER_ID)).thenThrow(new ContenidoNotFoundException(queryId));

        mockMvc.perform(get("/api/consultas/{id}", queryId))
                .andExpect(status().isNotFound());
    }
}
