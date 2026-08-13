package com.techcontent.ai.security;

import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class JwtAuthFilterTest {

    @Mock
    private JwtService jwtService;

    @Mock
    private FilterChain filterChain;

    @AfterEach
    void limpiarContexto() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void doFilter_sinAuthorization_continuaSinAutenticar() throws Exception {
        JwtAuthFilter filter = new JwtAuthFilter(jwtService);
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        filter.doFilter(request, response, filterChain);

        assertNull(SecurityContextHolder.getContext().getAuthentication());
        verify(filterChain).doFilter(request, response);
        verifyNoInteractions(jwtService);
    }

    @Test
    void doFilter_conTokenValido_autenticaUsuario() throws Exception {
        JwtAuthFilter filter = new JwtAuthFilter(jwtService);
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        UUID userId = UUID.randomUUID();
        request.addHeader("Authorization", "Bearer token-valido");

        when(jwtService.validateToken("token-valido")).thenReturn(JwtService.TokenValidationResult.VALID);
        when(jwtService.extractUserId("token-valido"))
                .thenReturn(userId.toString());
        when(jwtService.extractEmail("token-valido"))
                .thenReturn("usuario@example.com");
        when(jwtService.extractRole("token-valido"))
                .thenReturn("authenticated");

        filter.doFilter(request, response, filterChain);

        assertNotNull(SecurityContextHolder.getContext().getAuthentication());

        SupabaseUserDetails principal = (SupabaseUserDetails)
                SecurityContextHolder.getContext()
                        .getAuthentication()
                        .getPrincipal();

        assertEquals(userId, principal.getUserId());
        assertEquals("usuario@example.com", principal.getUsername());
        assertEquals("authenticated", principal.getRole());

        verify(filterChain).doFilter(request, response);
    }

    @Test
    void doFilter_conTokenInvalido_noAutenticaUsuario() throws Exception {
        JwtAuthFilter filter = new JwtAuthFilter(jwtService);
        MockHttpServletRequest request = new MockHttpServletRequest();
        MockHttpServletResponse response = new MockHttpServletResponse();

        request.addHeader("Authorization", "Bearer token-invalido");
        when(jwtService.validateToken("token-invalido")).thenReturn(JwtService.TokenValidationResult.INVALID);

        filter.doFilter(request, response, filterChain);

        assertNull(SecurityContextHolder.getContext().getAuthentication());
        verify(filterChain).doFilter(request, response);
        verify(jwtService, never()).extractUserId(anyString());
    }
}