package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.GrafoResponse;
import com.techcontent.ai.domain.service.GrafoService;
import com.techcontent.ai.security.JwtService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
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
                "grafo-id-123",
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
    @DisplayName("GET /api/grafos/historial - Debería retornar 200 OK con el listado de grafos")
    void obtenerHistorial_DeberiaRetornar200OK() throws Exception {
        when(grafoService.obtenerHistorial()).thenReturn(List.of(crearGrafoResponseDummy()));

        mockMvc.perform(get("/api/grafos/historial")
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(1));

        verify(grafoService).obtenerHistorial();
    }

    @Test
    @WithMockUser
    @DisplayName("GET /api/grafos/buscar - Debería retornar 200 OK al filtrar por rango de fechas")
    void buscarPorFechas_DeberiaRetornar200OK() throws Exception {
        String desde = "2026-01-01T00:00:00";
        String hasta = "2026-08-20T23:59:59";

        when(grafoService.buscarPorRangoFechas(any(LocalDateTime.class), any(LocalDateTime.class)))
                .thenReturn(List.of(crearGrafoResponseDummy()));

        mockMvc.perform(get("/api/grafos/buscar")
                        .param("desde", desde)
                        .param("hasta", hasta)
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk());

        verify(grafoService).buscarPorRangoFechas(any(LocalDateTime.class), any(LocalDateTime.class));
    }

    @Test
    @DisplayName("GET /api/grafos/actual - Debería retornar 401 Unauthorized sin usuario autenticado")
    void obtenerUltimo_SinAutenticacion_DeberiaRetornar401() throws Exception {
        mockMvc.perform(get("/api/grafos/actual"))
                .andExpect(status().isUnauthorized());
    }
}