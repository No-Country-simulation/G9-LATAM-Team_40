package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.GrafoResponse;
import com.techcontent.ai.domain.service.GrafoService;
import com.techcontent.ai.security.JwtService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(GrafoController.class)
class GrafoControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private GrafoService grafoService;

    @MockBean
    private JwtService jwtService;

    private GrafoResponse crearGrafoResponseDummy() {
        return new GrafoResponse(
                UUID.randomUUID().toString(),
                Collections.emptyMap(),
                LocalDateTime.now()
        );
    }

    @Test
    @WithMockUser
    @DisplayName("POST /api/grafos/sincronizar - Debería retornar 201 Created cuando sincroniza exitosamente")
    void sincronizar_DeberiaRetornar201Created() throws Exception {
        GrafoResponse mockResponse = crearGrafoResponseDummy();
        when(grafoService.sincronizarDesdeOci("archivo.json")).thenReturn(mockResponse);

        mockMvc.perform(post("/api/grafos/sincronizar")
                        .param("objectName", "archivo.json")
                        .with(csrf())
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isCreated());

        verify(grafoService).sincronizarDesdeOci("archivo.json");
    }

    @Test
    @WithMockUser
    @DisplayName("GET /api/grafos/actual - Debería retornar 200 OK con el último grafo")
    void obtenerUltimo_DeberiaRetornar200OK() throws Exception {
        GrafoResponse mockResponse = crearGrafoResponseDummy();
        when(grafoService.obtenerUltimo()).thenReturn(mockResponse);

        mockMvc.perform(get("/api/grafos/actual")
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk());

        verify(grafoService).obtenerUltimo();
    }

    @Test
    @WithMockUser
    @DisplayName("GET /api/grafos/{id} - Debería retornar 200 OK con el grafo específico por UUID")
    void obtenerPorId_DeberiaRetornar200OK() throws Exception {
        UUID id = UUID.randomUUID();
        GrafoResponse mockResponse = crearGrafoResponseDummy();
        when(grafoService.obtenerPorId(id)).thenReturn(mockResponse);

        mockMvc.perform(get("/api/grafos/id/{id}", id)
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk());

        verify(grafoService).obtenerPorId(id);
    }

    @Test
    @WithMockUser
    @DisplayName("GET /api/grafos/historial - Debería retornar 200 OK con la página de historial")
    void obtenerHistorial_DeberiaRetornar200OK() throws Exception {
        Page<GrafoResponse> pageMock = new PageImpl<>(List.of(crearGrafoResponseDummy()));
        when(grafoService.obtenerHistorial(any(Pageable.class))).thenReturn(pageMock);

        mockMvc.perform(get("/api/grafos/historial")
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content.length()").value(1));

        verify(grafoService).obtenerHistorial(any(Pageable.class));
    }

    @Test
    @WithMockUser
    @DisplayName("GET /api/grafos/buscarfecha - Debería retornar 200 OK al filtrar por rango de fechas")
    void buscarPorFechas_DeberiaRetornar200OK() throws Exception {
        String desdeParam = "2026-01-01";
        String hastaParam = "2026-08-20";

        LocalDate desdeExpected = LocalDate.of(2026, 1, 1);
        LocalDate hastaExpected = LocalDate.of(2026, 8, 20);

        when(grafoService.buscarPorRangoFechas(eq(desdeExpected), eq(hastaExpected)))
                .thenReturn(List.of(crearGrafoResponseDummy()));

        mockMvc.perform(get("/api/grafos/buscarfecha")
                        .param("desde", desdeParam)
                        .param("hasta", hastaParam)
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk());

        verify(grafoService).buscarPorRangoFechas(eq(desdeExpected), eq(hastaExpected));
    }

    @Test
    @DisplayName("GET /api/grafos/actual - Debería retornar 401 Unauthorized sin usuario autenticado")
    void obtenerUltimo_SinAutenticacion_DeberiaRetornar401() throws Exception {
        mockMvc.perform(get("/api/grafos/actual"))
                .andExpect(status().isUnauthorized());
    }
}