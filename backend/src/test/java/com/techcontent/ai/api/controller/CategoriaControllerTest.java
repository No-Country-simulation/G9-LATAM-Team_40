package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.service.CategoriaService;
import com.techcontent.ai.security.JwtService;
import com.techcontent.ai.security.SupabaseUserDetails;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.UUID;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(CategoriaController.class)
class CategoriaControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private CategoriaService categoriaService;

    @MockBean
    private JwtService jwtService;

    @Test
    @DisplayName("GET /api/categorias - Debería retornar 200 OK y la lista de categorías del usuario autenticado")
    void deberiaListarCategoriasDelUsuarioAutenticado() throws Exception {
        // Arrange
        UUID userId = UUID.randomUUID();
        SupabaseUserDetails userDetails = new SupabaseUserDetails(userId, "test@techcontent.com", "authenticated");

        List<CategoriaResponse> mockResponse = List.of(
                new CategoriaResponse("Leyes", 3L),
                new CategoriaResponse("Salud", 1L)
        );

        when(categoriaService.listarConConteo(userId)).thenReturn(mockResponse);

        // Act & Assert
        mockMvc.perform(get("/api/categorias")
                        .with(user(userDetails))
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].nombre").value("Leyes"))
                .andExpect(jsonPath("$[0].totalDocumentos").value(3))
                .andExpect(jsonPath("$[1].nombre").value("Salud"))
                .andExpect(jsonPath("$[1].totalDocumentos").value(1));

        verify(categoriaService).listarConConteo(userId);
    }
}