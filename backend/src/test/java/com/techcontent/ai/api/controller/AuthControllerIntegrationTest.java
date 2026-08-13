package com.techcontent.ai.api.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.exception.InvalidCredentialsException;
import com.techcontent.ai.integration.supabase.SupabaseAuthClient;
import com.techcontent.ai.integration.supabase.SupabaseAuthRequest;
import com.techcontent.ai.integration.supabase.SupabaseAuthResponse;
import com.techcontent.ai.security.JwtAuthFilter;
import com.techcontent.ai.security.JwtService;
import com.techcontent.ai.security.SecurityConfig;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(AuthController.class)
@Import({SecurityConfig.class, JwtAuthFilter.class})
class AuthControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private SupabaseAuthClient supabaseAuthClient;

    @MockBean
    private JwtService jwtService;

    @Test
    void POST_login_credencialesCorrectas_deberiaRetornar200ConToken() throws Exception {
        SupabaseAuthResponse authResponse = new SupabaseAuthResponse(
                "eyJhbGciOiJIUzI1NiJ9.test", "refresh-token-xyz", "bearer", 3600
        );
        when(supabaseAuthClient.signIn(any(SupabaseAuthRequest.class))).thenReturn(authResponse);

        SupabaseAuthRequest request = new SupabaseAuthRequest("user@example.com", "password123");

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.access_token").value("eyJhbGciOiJIUzI1NiJ9.test"))
                .andExpect(jsonPath("$.token_type").value("bearer"));
    }

    @Test
    void POST_login_credencialesIncorrectas_deberiaRetornar401() throws Exception {
        when(supabaseAuthClient.signIn(any(SupabaseAuthRequest.class)))
                .thenThrow(new InvalidCredentialsException("Credenciales incorrectas."));

        SupabaseAuthRequest request = new SupabaseAuthRequest("user@example.com", "wrong-password");

        mockMvc.perform(post("/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("UNAUTHORIZED"));
    }

    @Test
    void POST_register_datosValidos_deberiaRetornar200() throws Exception {
        SupabaseAuthResponse authResponse = new SupabaseAuthResponse(
                "nuevo-access-token", "nuevo-refresh-token", "bearer", 3600
        );
        when(supabaseAuthClient.signUp(any(SupabaseAuthRequest.class))).thenReturn(authResponse);

        SupabaseAuthRequest request = new SupabaseAuthRequest("nuevo@example.com", "password123");

        mockMvc.perform(post("/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.access_token").value("nuevo-access-token"));
    }

    @Test
    void POST_register_emailDuplicado_deberiaRetornar400() throws Exception {
        when(supabaseAuthClient.signUp(any(SupabaseAuthRequest.class)))
                .thenThrow(new IllegalArgumentException("Email ya registrado o datos invalidos."));

        SupabaseAuthRequest request = new SupabaseAuthRequest("existente@example.com", "password123");

        mockMvc.perform(post("/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("BAD_REQUEST"));
    }
}
