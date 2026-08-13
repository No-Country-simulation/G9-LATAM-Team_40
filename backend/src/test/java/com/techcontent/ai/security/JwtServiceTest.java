package com.techcontent.ai.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class JwtServiceTest {

    private static final String SECRET = "test-secret-key-for-jwt-signing-minimum-256-bits-xxxxxxxxxxxxxxxxx";
    private static final String USER_ID = "00000000-0000-0000-0000-000000000001";
    private static final String EMAIL = "test@example.com";

    private JwtService jwtService;
    private SecretKey secretKey;

    @BeforeEach
    void setUp() {
        jwtService = new JwtService(SECRET);
        secretKey = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));
    }

    private String buildToken(long expirationMs) {
        return Jwts.builder()
                .subject(USER_ID)
                .claim("email", EMAIL)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expirationMs))
                .signWith(secretKey)
                .compact();
    }

    @Test
    void validateToken_tokenValido_deberiaRetornarVALID() {
        String token = buildToken(60_000);
        assertThat(jwtService.validateToken(token)).isEqualTo(JwtService.TokenValidationResult.VALID);
    }

    @Test
    void validateToken_tokenExpirado_deberiaRetornarEXPIRED() {
        String token = buildToken(-1000); // ya expirado
        assertThat(jwtService.validateToken(token)).isEqualTo(JwtService.TokenValidationResult.EXPIRED);
    }

    @Test
    void validateToken_tokenConFirmaInvalida_deberiaRetornarINVALID() {
        SecretKey wrongKey = Keys.hmacShaKeyFor(
                "wrong-secret-key-completely-different-256-bits-xxxxxxxxxxxxxxxxxxxx".getBytes(StandardCharsets.UTF_8)
        );
        String tokenFirmadoMal = Jwts.builder()
                .subject(USER_ID)
                .expiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(wrongKey)
                .compact();

        assertThat(jwtService.validateToken(tokenFirmadoMal)).isEqualTo(JwtService.TokenValidationResult.INVALID);
    }

    @Test
    void validateToken_tokenMalformado_deberiaRetornarINVALID() {
        assertThat(jwtService.validateToken("esto.no.es.un.jwt")).isEqualTo(JwtService.TokenValidationResult.INVALID);
    }

    @Test
    void validateToken_sinSecretoConfigurado_deberiaRetornarINVALID() {
        JwtService sinSecreto = new JwtService("");
        assertThat(sinSecreto.validateToken("cualquier-token")).isEqualTo(JwtService.TokenValidationResult.INVALID);
    }

    @Test
    void isTokenValid_tokenValido_deberiaRetornarTrue() {
        assertThat(jwtService.isTokenValid(buildToken(60_000))).isTrue();
    }

    @Test
    void isTokenValid_tokenExpirado_deberiaRetornarFalse() {
        assertThat(jwtService.isTokenValid(buildToken(-1000))).isFalse();
    }

    @Test
    void extractUserId_deberiaRetornarElSubjectDelToken() {
        String token = buildToken(60_000);
        assertThat(jwtService.extractUserId(token)).isEqualTo(USER_ID);
    }

    @Test
    void extractEmail_deberiaRetornarElEmailDelToken() {
        String token = buildToken(60_000);
        assertThat(jwtService.extractEmail(token)).isEqualTo(EMAIL);
    }

    @Test
    void extractClaims_sinSecreto_deberiaLanzarIllegalState() {
        JwtService sinSecreto = new JwtService("");
        assertThatThrownBy(() -> sinSecreto.extractClaims("cualquier-token"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("JWT secret no configurado");
    }
}
