package com.techcontent.ai.api.controller;

import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import com.techcontent.ai.security.SupabaseUserDetails;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.RequestPostProcessor;

import java.util.UUID;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ArchivoControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ArchivoRepository archivoRepository;

    @MockBean
    private OciStorageClient ociStorageClient;

    private UUID userId;

    @BeforeEach
    void setUp() {
        archivoRepository.deleteAll();
        userId = UUID.randomUUID();

        when(ociStorageClient.upload(anyString(), anyString(), any(), anyString()))
                .thenReturn("https://storage.example.com/archivo-subido.pdf");
    }

    private RequestPostProcessor usuarioAutenticado() {
        SupabaseUserDetails userDetails = new SupabaseUserDetails(userId, "test@example.com");
        return SecurityMockMvcRequestPostProcessors.user(userDetails);
    }

    @Test
    void postArchivo_conArchivoValido_deberiaSubirloYRetornar200() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file",                
                "documento.pdf",
                "application/pdf",
                "contenido de prueba".getBytes()
        );

        mockMvc.perform(multipart("/api/archivos")
                        .file(file)
                        .with(usuarioAutenticado()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.nombre").value("documento.pdf"))
                .andExpect(jsonPath("$.url").value("https://storage.example.com/archivo-subido.pdf"))
                .andExpect(jsonPath("$.tipo").value("application/pdf"));
    }

    @Test
    void postArchivo_archivoVacio_deberiaRetornar400() throws Exception {
        MockMultipartFile fileVacio = new MockMultipartFile(
                "file", "vacio.pdf", "application/pdf", new byte[0]
        );

        mockMvc.perform(multipart("/api/archivos")
                        .file(fileVacio)
                        .with(usuarioAutenticado()))
                .andExpect(status().isBadRequest());
    }

    @Test
    void postArchivo_tipoNoPermitido_deberiaRetornar400() throws Exception {
        MockMultipartFile fileInvalido = new MockMultipartFile(
                "file", "imagen.png", "image/png", "contenido".getBytes()
        );

        mockMvc.perform(multipart("/api/archivos")
                        .file(fileInvalido)
                        .with(usuarioAutenticado()))
                .andExpect(status().isBadRequest());
    }

    @Test
    void postArchivo_sinAutenticacion_deberiaRetornar403() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "documento.pdf", "application/pdf", "contenido".getBytes()
        );

        mockMvc.perform(multipart("/api/archivos").file(file))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void getListar_deberiaDevolverSoloLosArchivosDelUsuarioAutenticado() throws Exception {

        MockMultipartFile file = new MockMultipartFile(
                "file", "mi-archivo.pdf", "application/pdf", "contenido".getBytes()
        );
        mockMvc.perform(multipart("/api/archivos")
                .file(file)
                .with(usuarioAutenticado()));

        mockMvc.perform(get("/api/archivos")
                        .with(usuarioAutenticado()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(1))
                .andExpect(jsonPath("$[0].nombre").value("mi-archivo.pdf"));
    }

    @Test
    void getObtenerPorId_archivoExistente_deberiaDevolverlo() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "encontrame.pdf", "application/pdf", "contenido".getBytes()
        );
        String responseJson = mockMvc.perform(multipart("/api/archivos")
                        .file(file)
                        .with(usuarioAutenticado()))
                .andReturn().getResponse().getContentAsString();

        String id = com.jayway.jsonpath.JsonPath.read(responseJson, "$.id");

        mockMvc.perform(get("/api/archivos/{id}", id)
                        .with(usuarioAutenticado()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.nombre").value("encontrame.pdf"));
    }

    @Test
    void getObtenerPorId_archivoInexistente_deberiaRetornar404() throws Exception {
        UUID idInexistente = UUID.randomUUID();

        mockMvc.perform(get("/api/archivos/{id}", idInexistente)
                        .with(usuarioAutenticado()))
                .andExpect(status().isNotFound());
    }
}