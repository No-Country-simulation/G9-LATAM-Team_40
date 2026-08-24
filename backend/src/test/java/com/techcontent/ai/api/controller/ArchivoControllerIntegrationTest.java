package com.techcontent.ai.api.controller;

import com.techcontent.ai.domain.service.ArchivoDownload;
import com.techcontent.ai.domain.service.ArchivoService;
import com.techcontent.ai.security.JwtService;
import com.techcontent.ai.security.SupabaseUserDetails;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.test.web.servlet.MockMvc;

import java.io.ByteArrayInputStream;
import java.util.UUID;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ArchivoController.class)
@AutoConfigureMockMvc(addFilters = false)
class ArchivoControllerIntegrationTest {

    @Autowired private MockMvc mockMvc;
    @MockBean private ArchivoService archivoService;
    @MockBean private JwtService jwtService;

    private static final UUID USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");
    private static final UUID FILE_ID = UUID.fromString("00000000-0000-0000-0000-000000000002");

    @Test
    void descargar_usaRespuestaStreamingYContentDisposition() throws Exception {
        SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                new SupabaseUserDetails(USER_ID, "user@example.com", "authenticated"), null));
        when(archivoService.descargar(FILE_ID, USER_ID))
                .thenReturn(new ArchivoDownload(new ByteArrayInputStream("data".getBytes()), 4L, "text/plain", "manual.txt"));

        mockMvc.perform(get("/api/archivos/{id}/descarga", FILE_ID))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Disposition", org.hamcrest.Matchers.containsString("manual.txt")));
    }
}
