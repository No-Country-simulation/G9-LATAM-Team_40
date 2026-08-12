package com.techcontent.ai.security;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.access.AccessDeniedException;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class JwtAccessDeniedHandlerTest {

    @Test
    void handle_accesoDenegado_retorna403EnFormatoJson() throws Exception {
        JwtAccessDeniedHandler handler = new JwtAccessDeniedHandler();
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        handler.handle(
                request,
                response,
                new AccessDeniedException("Sin permisos")
        );

        assertEquals(403, response.getStatus());
        assertEquals("application/json", response.getContentType());
        assertTrue(response.getContentAsString().contains("\"error\":\"FORBIDDEN\""));
        assertTrue(response.getContentAsString().contains(
                "\"mensaje\":\"No tenes permisos para acceder a este recurso\""
        ));
    }
}