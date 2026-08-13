
package com.techcontent.ai.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.api.exception.ErrorResponse;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void commence(HttpServletRequest request,
                          HttpServletResponse response,
                          AuthenticationException authException) throws IOException, ServletException {

        response.setStatus(HttpStatus.UNAUTHORIZED.value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);

        ErrorResponse errorResponse = new ErrorResponse(
                "UNAUTHORIZED",
                "No se proporciono un token valido de autenticacion"
        );

        response.getWriter().write(objectMapper.writeValueAsString(errorResponse));
    }
}