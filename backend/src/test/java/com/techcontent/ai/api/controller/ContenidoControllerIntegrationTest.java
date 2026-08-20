package com.techcontent.ai.api.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.request.ContenidoRequest;
import com.techcontent.ai.api.dto.response.ContenidoResponse;
import com.techcontent.ai.domain.service.ContenidoService;
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
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(ContenidoController.class)
@Import({SecurityConfig.class, JwtAuthFilter.class, JwtAuthenticationEntryPoint.class, JwtAccessDeniedHandler.class})
class ContenidoControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ContenidoService contenidoService;

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
        ContenidoRequest request = new ContenidoRequest("Titulo", "Texto de prueba con mas de veinte caracteres");

        mockMvc.perform(post("/api/contenido")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("UNAUTHORIZED"));
    }

    @Test
    void POST_conJwtExpirado_deberiaRetornar401ConMensajeExpirado() throws Exception {
        when(jwtService.validateToken("expired-token")).thenReturn(JwtService.TokenValidationResult.EXPIRED);

        ContenidoRequest request = new ContenidoRequest("Titulo", "Texto de prueba con mas de veinte caracteres");

        mockMvc.perform(post("/api/contenido")
                        .header("Authorization", "Bearer expired-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(content().string(org.hamcrest.Matchers.containsString("expirado")));
    }

    @Test
    void POST_conJwtValidoYBodyValido_deberiaRetornar200ConLaRespuestaDeClasificacion() throws Exception {
        ContenidoRequest request = new ContenidoRequest("Titulo de prueba", "Texto de prueba con mas de veinte caracteres para validacion");

        // Se instancian los 8 parámetros correspondientes al nuevo ContenidoResponse
        ContenidoResponse mockResponse = new ContenidoResponse(
                UUID.randomUUID().toString(),
                "Backend",
                0.95,
                List.of("Java", "Spring"),
                List.of(),
                "Spring Boot simplifica el desarrollo.",
                List.of(),
                LocalDateTime.now()
        );

        when(contenidoService.clasificar(any(), any(UUID.class))).thenReturn(mockResponse);

        mockMvc.perform(post("/api/contenido")
                        .header("Authorization", "Bearer " + VALID_TOKEN)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.categoria").value("Backend"))
                .andExpect(jsonPath("$.probabilidad").value(0.95))
                .andExpect(jsonPath("$.palabras_clave[0]").value("Java"))
                .andExpect(jsonPath("$.respuesta").value("Spring Boot simplifica el desarrollo."));
    }

    @Test
    void POST_conJwtValidoYBodyInvalido_deberiaRetornar400ConValidationError() throws Exception {
        ContenidoRequest requestInvalido = new ContenidoRequest("", "corto");

        mockMvc.perform(post("/api/contenido")
                        .header("Authorization", "Bearer " + VALID_TOKEN)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(requestInvalido)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_ERROR"));
    }
}