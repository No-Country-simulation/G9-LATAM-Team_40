package com.techcontent.ai.api.exception;

import com.techcontent.ai.integration.ml.MlServiceException;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class GlobalExceptionHandlerTest {

    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        LocalValidatorFactoryBean validator = new LocalValidatorFactoryBean();
        validator.afterPropertiesSet();

        mockMvc = MockMvcBuilders
                .standaloneSetup(new ThrowingController())
                .setControllerAdvice(new GlobalExceptionHandler())
                .setValidator(validator)
                .build();
    }

    @RestController
    @RequestMapping("/test-ex")
    static class ThrowingController {

        record TestBody(@NotBlank String field) {}

        @PostMapping("/validation")
        public ResponseEntity<Void> validation(@Valid @RequestBody TestBody body) {
            return ResponseEntity.ok().build();
        }

        @GetMapping("/contenido-not-found")
        public ResponseEntity<Void> contenidoNotFound() {
            throw new ContenidoNotFoundException(UUID.fromString("00000000-0000-0000-0000-000000000001"));
        }

        @GetMapping("/archivo-not-found")
        public ResponseEntity<Void> archivoNotFound() {
            throw new ArchivoNotFoundException(UUID.fromString("00000000-0000-0000-0000-000000000002"));
        }

        @GetMapping("/bad-request")
        public ResponseEntity<Void> badRequest() {
            throw new IllegalArgumentException("argumento invalido de prueba");
        }

        @GetMapping("/ml-error")
        public ResponseEntity<Void> mlError() {
            throw new MlServiceException("ML service unavailable");
        }

        @GetMapping("/invalid-credentials")
        public ResponseEntity<Void> invalidCredentials() {
            throw new InvalidCredentialsException("Credenciales incorrectas.");
        }

        @GetMapping("/server-error")
        public ResponseEntity<Void> serverError() {
            throw new RuntimeException("error inesperado en el servidor");
        }
    }

    @Test
    void validationError_deberiaRetornar400ConValidationError() throws Exception {
        mockMvc.perform(post("/test-ex/validation")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"field\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("VALIDATION_ERROR"))
                .andExpect(jsonPath("$.mensaje").exists());
    }

    @Test
    void contenidoNotFound_deberiaRetornar404ConNotFound() throws Exception {
        mockMvc.perform(get("/test-ex/contenido-not-found"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("NOT_FOUND"))
                .andExpect(jsonPath("$.mensaje").value(
                        "Contenido no encontrado con id: 00000000-0000-0000-0000-000000000001"
                ));
    }

    @Test
    void archivoNotFound_deberiaRetornar404ConNotFound() throws Exception {
        mockMvc.perform(get("/test-ex/archivo-not-found"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("NOT_FOUND"));
    }

    @Test
    void badRequest_deberiaRetornar400ConBadRequest() throws Exception {
        mockMvc.perform(get("/test-ex/bad-request"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").value("BAD_REQUEST"))
                .andExpect(jsonPath("$.mensaje").value("argumento invalido de prueba"));
    }

    @Test
    void mlError_deberiaRetornar503ConServiceUnavailable() throws Exception {
        mockMvc.perform(get("/test-ex/ml-error"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.error").value("SERVICE_UNAVAILABLE"));
    }

    @Test
    void invalidCredentials_deberiaRetornar401ConUnauthorized() throws Exception {
        mockMvc.perform(get("/test-ex/invalid-credentials"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.error").value("UNAUTHORIZED"))
                .andExpect(jsonPath("$.mensaje").value("Credenciales incorrectas."));
    }

    @Test
    void serverError_deberiaRetornar500ConInternalError() throws Exception {
        mockMvc.perform(get("/test-ex/server-error"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").value("INTERNAL_ERROR"))
                .andExpect(jsonPath("$.mensaje").value("Error interno del servidor"));
    }
}
