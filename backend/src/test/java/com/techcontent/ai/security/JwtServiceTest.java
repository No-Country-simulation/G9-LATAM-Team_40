package com.techcontent.ai.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;

class JwtServiceTest {

    private static final String TEST_SECRET = "clave-secreta-de-prueba-para-tests-1234567890";

    private JwtService jwtService;
    private SecretKey secretKeyDePrueba;

    @BeforeEach
    void setUp() {
   
        jwtService = new JwtService(TEST_SECRET);
        secretKeyDePrueba = Keys.hmacShaKeyFor(TEST_SECRET.getBytes(StandardCharsets.UTF_8));
    }

    private String generarTokenDePrueba(String userId, String email, Date expiracion) {
        return Jwts.builder()
                .subject(userId)
                .claim("email", email)
                .issuedAt(new Date())
                .expiration(expiracion)
                .signWith(secretKeyDePrueba)
                .compact();
    }

    @Test
    void isTokenValid_conTokenFirmadoCorrectamente_deberiaRetornarTrue() {
        String token = generarTokenDePrueba(
                "user-123",
                "test@example.com",
                new Date(System.currentTimeMillis() + 3_600_000)
        );

        boolean esValido = jwtService.isTokenValid(token);

        assertTrue(esValido);
    }

    @Test
    void isTokenValid_conTokenExpirado_deberiaRetornarFalse() {
  
        String tokenExpirado = generarTokenDePrueba(
                "user-123",
                "test@example.com",
                new Date(System.currentTimeMillis() - 3_600_000)
        );

        boolean esValido = jwtService.isTokenValid(tokenExpirado);

        assertFalse(esValido);
    }

    @Test
    void isTokenValid_conTokenFirmadoConOtraClave_deberiaRetornarFalse() {
 
        SecretKey otraClave = Keys.hmacShaKeyFor("otra-clave-completamente-diferente-9999999".getBytes(StandardCharsets.UTF_8));
        String tokenFalsificado = Jwts.builder()
                .subject("user-123")
                .claim("email", "hacker@example.com")
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + 3_600_000))
                .signWith(otraClave)
                .compact();

        boolean esValido = jwtService.isTokenValid(tokenFalsificado);

        assertFalse(esValido);
    }

    @Test
    void isTokenValid_conTokenMalformado_deberiaRetornarFalse() {

        boolean esValido = jwtService.isTokenValid("esto-no-es-un-token-jwt-valido");

        assertFalse(esValido);
    }

    @Test
    void extractUserId_conTokenValido_deberiaDevolverElSubject() {
        String token = generarTokenDePrueba(
                "user-456",
                "otro@example.com",
                new Date(System.currentTimeMillis() + 3_600_000)
        );

        String userId = jwtService.extractUserId(token);

        assertEquals("user-456", userId);
    }

    @Test
    void extractEmail_conTokenValido_deberiaDevolverElEmail() {
        String token = generarTokenDePrueba(
                "user-789",
                "correo@example.com",
                new Date(System.currentTimeMillis() + 3_600_000)
        );

        String email = jwtService.extractEmail(token);

        assertEquals("correo@example.com", email);
    }

    @Test
    void constructor_sinSecretoConfigurado_deberiaRechazarTodaValidacion() {

        JwtService serviceSinSecreto = new JwtService("");

        String cualquierToken = generarTokenDePrueba(
                "user-123", "test@example.com", new Date(System.currentTimeMillis() + 3_600_000)
        );

        assertFalse(serviceSinSecreto.isTokenValid(cualquierToken));
    }

    @Test
    void extractClaims_sinSecretoConfigurado_deberiaLanzarIllegalStateException() {
        JwtService serviceSinSecreto = new JwtService(null);

        assertThrows(
                IllegalStateException.class,
                () -> serviceSinSecreto.extractClaims("cualquier-token")
        );
    }
} 
