package com.techcontent.ai.api.controller;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.domain.service.ArchivoService;
import com.techcontent.ai.security.JwtAuthFilter;
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
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ArchivoController.class)
@Import({SecurityConfig.class, JwtAuthFilter.class})
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
    void POST_conJwtValidoYArchivoValido_deberiaRetornar200() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "documento.pdf", "application/pdf", "contenido pdf".getBytes()
        );
        ArchivoResponse mockResponse = new ArchivoResponse(
                UUID.randomUUID().toString(), "documento.pdf",
                "https://oci/test/documento.pdf", 1024L,
                "application/pdf", LocalDateTime.now()
        );

        when(archivoService.subir(any(), any(UUID.class))).thenReturn(mockResponse);

        mockMvc.perform(multipart("/api/archivos")
                        .file(file)
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.nombre").value("documento.pdf"))
                .andExpect(jsonPath("$.tipo").value("application/pdf"));
    }

    @Test
    void GET_conJwtValido_deberiaRetornarListaDeArchivos() throws Exception {
        ArchivoResponse archivo = new ArchivoResponse(
                UUID.randomUUID().toString(), "doc.pdf",
                "https://oci/test/doc.pdf", 2048L,
                "application/pdf", LocalDateTime.now()
        );
        when(archivoService.listar(any(UUID.class))).thenReturn(List.of(archivo));

        mockMvc.perform(get("/api/archivos")
                        .header("Authorization", "Bearer " + VALID_TOKEN))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].nombre").value("doc.pdf"));
    }

    @Test
    void GET_sinJwt_deberiaRetornar401() throws Exception {
        mockMvc.perform(get("/api/archivos"))
                .andExpect(status().isUnauthorized());
    }
}
