package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.api.dto.response.PaginaResponse;
import com.techcontent.ai.api.exception.ArchivoNotFoundException;
import com.techcontent.ai.domain.service.ArchivoService;
import com.techcontent.ai.security.JwtAccessDeniedHandler;
import com.techcontent.ai.security.JwtAuthFilter;
import com.techcontent.ai.security.JwtAuthenticationEntryPoint;
import com.techcontent.ai.security.JwtService;
import com.techcontent.ai.security.SecurityConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.nullable;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ArchivoController.class)
@Import({SecurityConfig.class, JwtAuthFilter.class, JwtAuthenticationEntryPoint.class, JwtAccessDeniedHandler.class})
class ArchivoControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ArchivoService archivoService;

    @MockBean
    private JwtService jwtService;

    private static final UUID TEST_USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");
    private static final String VALID_TOKEN = "valid-test-token";

    @BeforeEach
    void setUp() {
        when(jwtService.validateToken(VALID_TOKEN)).thenReturn(JwtService.TokenValidationResult.VALID);
        when(jwtService.extractUserId(VALID_TOKEN)).thenReturn(TEST_USER_ID.toString());
        when(jwtService.extractEmail(VALID_TOKEN)).thenReturn("test@example.com");
    }

    @Test
    void POST_sinJwt_deberiaRetornar401() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "test.pdf", "application/pdf", "contenido".getBytes()
        );

        mockMvc.perform(multipart("/api/archivos").file(file))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void POST_conJwtValidoYArchivoValido_deberiaRetornar201() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "documento.pdf", "application/pdf", "contenido pdf".getBytes()
        );
        ArchivoResponse mockResponse = new ArchivoResponse(
                UUID.randomUUID().toString(), "documento.pdf",
                "https://oci/test/documento.pdf", 1024L,
                "application/pdf", LocalDateTime.now()
        );

        // Se agrega nullable(String.class) o any() para soportar el 3er parametro (categoria)
        when(archivoService.subir(any(), any(UUID.class), nullable(String.class))).thenReturn(mockResponse);

        mockMvc.perform(multipart("/api/archivos")
                        .file(file)
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isCreated()) // Cambiado de isOk() a isCreated() (201)
                .andExpect(jsonPath("$.nombre").value("documento.pdf"))
                .andExpect(jsonPath("$.tipo").value("application/pdf"));

        verify(archivoService).subir(any(), eq(TEST_USER_ID), eq(null));
    }

    @Test
    void POST_conCategoria_deberiaDelegarCategoriaAService() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "iso-9001.pdf", "application/pdf", "contenido pdf".getBytes()
        );
        ArchivoResponse mockResponse = new ArchivoResponse(
                UUID.randomUUID().toString(), "iso-9001.pdf",
                "https://oci/test/iso-9001.pdf", 1024L,
                "application/pdf", LocalDateTime.now()
        );

        when(archivoService.subir(any(), any(UUID.class), eq("ISO"))).thenReturn(mockResponse);

        mockMvc.perform(multipart("/api/archivos")
                        .file(file)
                        .param("categoria", "ISO")
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.nombre").value("iso-9001.pdf"));

        verify(archivoService).subir(any(), eq(TEST_USER_ID), eq("ISO"));
    }

    @Test
    void GET_conJwtValido_deberiaRetornarListaDeArchivos() throws Exception {
        ArchivoResponse archivo = new ArchivoResponse(
                UUID.randomUUID().toString(), "doc.pdf",
                "https://oci/test/doc.pdf", 2048L,
                "application/pdf", LocalDateTime.now()
        );
        PaginaResponse<ArchivoResponse> pagina = new PaginaResponse<>(
                List.of(archivo), 0, 20, 1, 1
        );
        when(archivoService.listar(any(UUID.class), eq(0), eq(20), eq(""), eq("")))
                .thenReturn(pagina);

        mockMvc.perform(get("/api/archivos")
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items[0].nombre").value("doc.pdf"))
                .andExpect(jsonPath("$.page").value(0))
                .andExpect(jsonPath("$.size").value(20))
                .andExpect(jsonPath("$.totalElements").value(1))
                .andExpect(jsonPath("$.totalPages").value(1));

        verify(archivoService).listar(TEST_USER_ID, 0, 20, "", "");
    }

    @Test
    void GET_conPaginacionPersonalizada_deberiaDelegarParametros() throws Exception {
        PaginaResponse<ArchivoResponse> pagina = new PaginaResponse<>(
                List.of(), 2, 5, 0, 0
        );
        when(archivoService.listar(any(UUID.class), eq(2), eq(5), eq(""), eq("")))
                .thenReturn(pagina);

        mockMvc.perform(get("/api/archivos")
                        .param("page", "2")
                        .param("size", "5")
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items").isEmpty())
                .andExpect(jsonPath("$.page").value(2))
                .andExpect(jsonPath("$.size").value(5));

        verify(archivoService).listar(TEST_USER_ID, 2, 5, "", "");
    }

    @Test
    void GET_conBusquedaPorNombre_deberiaDelegarQuery() throws Exception {
        PaginaResponse<ArchivoResponse> pagina = new PaginaResponse<>(
                List.of(), 0, 20, 0, 0
        );
        when(archivoService.listar(any(UUID.class), eq(0), eq(20), eq("manual"), eq("")))
                .thenReturn(pagina);

        mockMvc.perform(get("/api/archivos")
                        .param("q", "manual")
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items").isEmpty());

        verify(archivoService).listar(TEST_USER_ID, 0, 20, "manual", "");
    }

    @Test
    void GET_conBusquedaYTipo_deberiaDelegarFiltros() throws Exception {
        PaginaResponse<ArchivoResponse> pagina = new PaginaResponse<>(
                List.of(), 0, 5, 0, 0
        );
        when(archivoService.listar(
                any(UUID.class), eq(0), eq(5), eq("manual"), eq("pdf")))
                .thenReturn(pagina);

        mockMvc.perform(get("/api/archivos")
                        .param("page", "0")
                        .param("size", "5")
                        .param("q", "manual")
                        .param("tipo", "pdf")
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.items").isEmpty())
                .andExpect(jsonPath("$.size").value(5));

        verify(archivoService).listar(TEST_USER_ID, 0, 5, "manual", "pdf");
    }

    @Test
    void GET_sinJwt_deberiaRetornar401() throws Exception {
        mockMvc.perform(get("/api/archivos"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void DELETE_conJwtValido_deberiaRetornar204() throws Exception {
        UUID archivoId = UUID.fromString("00000000-0000-0000-0000-000000000002");

        mockMvc.perform(delete("/api/archivos/{id}", archivoId)
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isNoContent())
                .andExpect(content().string(""));

        verify(archivoService).eliminar(archivoId, TEST_USER_ID);
    }

    @Test
    void DELETE_sinJwt_deberiaRetornar401() throws Exception {
        UUID archivoId = UUID.fromString("00000000-0000-0000-0000-000000000002");

        mockMvc.perform(delete("/api/archivos/{id}", archivoId))
                .andExpect(status().isUnauthorized());

        verifyNoInteractions(archivoService);
    }

    @Test
    void DELETE_archivoNoEncontrado_deberiaRetornar404() throws Exception {
        UUID archivoId = UUID.fromString("00000000-0000-0000-0000-000000000099");
        doThrow(new ArchivoNotFoundException(archivoId))
                .when(archivoService).eliminar(archivoId, TEST_USER_ID);

        mockMvc.perform(delete("/api/archivos/{id}", archivoId)
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("NOT_FOUND"))
                .andExpect(jsonPath("$.mensaje").value(
                        "Archivo no encontrado con id: " + archivoId
                ));

        verify(archivoService).eliminar(archivoId, TEST_USER_ID);
    }
}