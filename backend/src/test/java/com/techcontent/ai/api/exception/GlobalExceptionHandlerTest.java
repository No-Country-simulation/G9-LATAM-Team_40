package com.techcontent.ai.api.exception;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;

import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class GlobalExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    void handleContenidoNotFound_deberiaRetornar404ConMensaje() {

        UUID id = UUID.randomUUID();
        ContenidoNotFoundException ex = new ContenidoNotFoundException(id);

        ResponseEntity<ErrorResponse> response = handler.handleContenidoNotFound(ex);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("NOT_FOUND", response.getBody().error());
        assertTrue(response.getBody().mensaje().contains(id.toString()));
    }

    @Test
    void handleArchivoNotFound_deberiaRetornar404ConMensaje() {
        UUID id = UUID.randomUUID();
        ArchivoNotFoundException ex = new ArchivoNotFoundException(id);

        ResponseEntity<ErrorResponse> response = handler.handleArchivoNotFound(ex);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertEquals("NOT_FOUND", response.getBody().error());
    }

    @Test
    void handleIllegalArgument_deberiaRetornar400ConMensajeOriginal() {
        IllegalArgumentException ex = new IllegalArgumentException("El archivo no puede estar vacio");

        ResponseEntity<ErrorResponse> response = handler.handleIllegalArgument(ex);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("BAD_REQUEST", response.getBody().error());
        assertEquals("El archivo no puede estar vacio", response.getBody().mensaje());
    }

    @Test
    void handleGeneral_deberiaRetornar500SinExponerElMensajeInterno() {

        Exception ex = new RuntimeException("NullPointerException en la linea 42, detalle sensible de stacktrace");

        ResponseEntity<ErrorResponse> response = handler.handleGeneral(ex);

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, response.getStatusCode());
        assertEquals("INTERNAL_ERROR", response.getBody().error());
        assertEquals("Error interno del servidor", response.getBody().mensaje());
    }

    @Test
    void handleValidation_deberiaJuntarTodosLosErroresDeCampoEnUnMensaje() {

        MethodArgumentNotValidException ex = mock(MethodArgumentNotValidException.class);
        BindingResult bindingResult = mock(BindingResult.class);

        FieldError error1 = new FieldError("contenidoRequest", "titulo", "El titulo es requerido");
        FieldError error2 = new FieldError("contenidoRequest", "texto", "El texto debe tener al menos 20 caracteres");

        when(ex.getBindingResult()).thenReturn(bindingResult);
        when(bindingResult.getFieldErrors()).thenReturn(List.of(error1, error2));

        ResponseEntity<ErrorResponse> response = handler.handleValidation(ex);

        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertEquals("VALIDATION_ERROR", response.getBody().error());
        
        assertTrue(response.getBody().mensaje().contains("titulo: El titulo es requerido"));
        assertTrue(response.getBody().mensaje().contains("texto: El texto debe tener al menos 20 caracteres"));
    }
}