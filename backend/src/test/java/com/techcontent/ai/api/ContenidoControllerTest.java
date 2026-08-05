package com.techcontent.ai.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.dto.ContenidoRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ContenidoController.class)
class ContenidoControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void deberiaCrearContenidoExitosamenteCuandoRequestEsValido() throws Exception {
        ContenidoRequest request = new ContenidoRequest("Spring Boot API", "Este es un texto de prueba válido para la API REST.");

        mockMvc.perform(post("/api/contenidos")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.titulo").value("Spring Boot API"))
                .andExpect(jsonPath("$.autor").value("Usuario QA"));
    }

    @Test
    void deberiaRetornarBadRequestCuandoTituloEstaVacio() throws Exception {
        // Título vacío y texto corto para forzar los errores de validación (@NotBlank y @Size)
        ContenidoRequest request = new ContenidoRequest("", "Corto");

        mockMvc.perform(post("/api/contenidos")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void deberiaListarContenidos() throws Exception {
        mockMvc.perform(get("/api/contenidos"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].titulo").exists());
    }
}