package com.techcontent.ai.api.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.dto.request.ContenidoLoteRequest;
import com.techcontent.ai.api.dto.request.ContenidoRequest;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.ml.MlResponse;
import com.techcontent.ai.security.SupabaseUserDetails;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.RequestPostProcessor;

import java.util.List;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;


@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ContenidoControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private ContenidoRepository contenidoRepository;

    @MockBean
    private MlClient mlClient;

    private UUID userId;

    @BeforeEach
    void setUp() {

        contenidoRepository.deleteAll();

        userId = UUID.randomUUID();

        when(mlClient.predict(anyString())).thenReturn(
                new MlResponse("Backend", 0.90, List.of("spring", "java"))
        );
    }

    private RequestPostProcessor usuarioAutenticado() {
        SupabaseUserDetails userDetails = new SupabaseUserDetails(userId, "test@example.com");
        return SecurityMockMvcRequestPostProcessors.user(userDetails);
    }

    @Test
    void postContenido_conDatosValidos_deberiaRetornar200YElContenidoClasificado() throws Exception {
        ContenidoRequest request = new ContenidoRequest(
                "Titulo de prueba",
                "Este es un texto de prueba con mas de veinte caracteres"
        );

        mockMvc.perform(post("/api/contenido")
                        .with(usuarioAutenticado())
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.categoria").value("Backend"))
                .andExpect(jsonPath("$.probabilidad").value(0.90))
                .andExpect(jsonPath("$.palabrasClave[0]").value("spring"));
    }

    @Test
    void postContenido_sinTitulo_deberiaRetornar400() throws Exception {

        String jsonInvalido = """
                {"titulo": "", "texto": "Este es un texto de prueba con mas de veinte caracteres"}
                """;

        mockMvc.perform(post("/api/contenido")
                        .with(usuarioAutenticado())
                        .contentType("application/json")
                        .content(jsonInvalido))
                .andExpect(status().isBadRequest());
    }

    @Test
    void postContenido_conTextoMuyCorto_deberiaRetornar400() throws Exception {
        String jsonInvalido = """
                {"titulo": "Titulo valido", "texto": "corto"}
                """;

        mockMvc.perform(post("/api/contenido")
                        .with(usuarioAutenticado())
                        .contentType("application/json")
                        .content(jsonInvalido))
                .andExpect(status().isBadRequest());
    }

    @Test
    void postContenido_sinAutenticacion_deberiaRetornar403() throws Exception {
 
        ContenidoRequest request = new ContenidoRequest(
                "Titulo", "Este es un texto de prueba con mas de veinte caracteres"
        );

        mockMvc.perform(post("/api/contenido")
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void postContenidoLote_conListaValida_deberiaClasificarTodos() throws Exception {
        ContenidoRequest item1 = new ContenidoRequest("Titulo 1", "Primer texto de prueba con longitud suficiente");
        ContenidoRequest item2 = new ContenidoRequest("Titulo 2", "Segundo texto de prueba con longitud suficiente");
        ContenidoLoteRequest lote = new ContenidoLoteRequest(List.of(item1, item2));

        mockMvc.perform(post("/api/contenido/lote")
                        .with(usuarioAutenticado())
                        .contentType("application/json")
                        .content(objectMapper.writeValueAsString(lote)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2));
    }

    @Test
    void postContenidoLote_conListaVacia_deberiaRetornar400() throws Exception {
        String jsonListaVacia = """
                {"contenidos": []}
                """;

        mockMvc.perform(post("/api/contenido/lote")
                        .with(usuarioAutenticado())
                        .contentType("application/json")
                        .content(jsonListaVacia))
                .andExpect(status().isBadRequest());
    }

    @Test
    void getBuscar_deberiaEncontrarContenidoPorPalabraClave() throws Exception {

        ContenidoRequest request = new ContenidoRequest(
                "Guia de Spring Boot",
                "Un texto largo explicando como configurar Spring Boot paso a paso"
        );
        mockMvc.perform(post("/api/contenido")
                .with(usuarioAutenticado())
                .contentType("application/json")
                .content(objectMapper.writeValueAsString(request)));

        mockMvc.perform(get("/api/contenido/buscar")
                        .with(usuarioAutenticado())
                        .param("q", "spring"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(1));
    }

    @Test
    void getListar_deberiaDevolverSoloLosContenidosDelUsuarioAutenticado() throws Exception {

        ContenidoRequest request = new ContenidoRequest(
                "Mi contenido", "Texto de prueba con longitud suficiente para pasar"
        );
        mockMvc.perform(post("/api/contenido")
                .with(usuarioAutenticado())
                .contentType("application/json")
                .content(objectMapper.writeValueAsString(request)));

        mockMvc.perform(get("/api/contenido")
                        .with(usuarioAutenticado()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(1));
    }
}