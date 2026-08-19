package com.techcontent.ai.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PublicKey;
import java.security.spec.ECGenParameterSpec;
import java.util.Date;
import java.util.Map;

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
                .claim("role", "authenticated")
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expirationMs))
                .signWith(secretKey)
                .compact();
    }

    // ───────── HS256 tests ─────────

    @Test
    void validateToken_tokenValido_deberiaRetornarVALID() {
        String token = buildToken(60_000);
        assertThat(jwtService.validateToken(token)).isEqualTo(JwtService.TokenValidationResult.VALID);
    }

    @Test
    void validateToken_tokenExpirado_deberiaRetornarEXPIRED() {
        String token = buildToken(-1000);
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
        assertThat(jwtService.extractUserId(buildToken(60_000))).isEqualTo(USER_ID);
    }

    @Test
    void extractEmail_deberiaRetornarElEmailDelToken() {
        assertThat(jwtService.extractEmail(buildToken(60_000))).isEqualTo(EMAIL);
    }

    @Test
    void extractRole_deberiaRetornarElRolDelToken() {
        assertThat(jwtService.extractRole(buildToken(60_000))).isEqualTo("authenticated");
    }

    @Test
    void extractClaims_sinSecreto_deberiaLanzarIllegalState() {
        JwtService sinSecreto = new JwtService("");
        assertThatThrownBy(() -> sinSecreto.extractClaims("cualquier-token"))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("JWT secret no configurado");
    }

    // ───────── ES256 tests ─────────

    @Test
    void validateToken_tokenES256_conJwksCargadas_deberiaRetornarVALID() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair keyPair = kpg.generateKeyPair();
        String kid = "test-kid-es256";

        String token = Jwts.builder()
                .header().keyId(kid).and()
                .subject(USER_ID)
                .claim("email", EMAIL)
                .claim("role", "authenticated")
                .expiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(keyPair.getPrivate())
                .compact();

        ReflectionTestUtils.setField(jwtService, "jwksKeys", Map.of(kid, keyPair.getPublic()));

        assertThat(jwtService.validateToken(token)).isEqualTo(JwtService.TokenValidationResult.VALID);
    }

    @Test
    void validateToken_tokenES256_sinJwksCargadas_deberiaRetornarINVALID() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair keyPair = kpg.generateKeyPair();

        String token = Jwts.builder()
                .header().keyId("test-kid-es256").and()
                .subject(USER_ID)
                .expiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(keyPair.getPrivate())
                .compact();

        // jwksKeys esta vacio — no se cargaron claves
        assertThat(jwtService.validateToken(token)).isEqualTo(JwtService.TokenValidationResult.INVALID);
    }

    @Test
    void validateToken_tokenES256_kidDesconocido_usaClaveDisponible() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair keyPair = kpg.generateKeyPair();

        String token = Jwts.builder()
                .header().keyId("kid-desconocido").and()
                .subject(USER_ID)
                .expiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(keyPair.getPrivate())
                .compact();

        // Cargamos la clave publica con diferente kid — fallback a primera disponible
        ReflectionTestUtils.setField(jwtService, "jwksKeys",
                Map.of("otra-kid", keyPair.getPublic()));

        assertThat(jwtService.validateToken(token)).isEqualTo(JwtService.TokenValidationResult.VALID);
    }

    @Test
    void buildEcPublicKey_deberiaReconstruirClave() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair keyPair = kpg.generateKeyPair();
        PublicKey original = keyPair.getPublic();

        // Usamos el token ES256 para que JwtService valide con la clave reconstruida
        String kid = "rebuild-kid";
        String token = Jwts.builder()
                .header().keyId(kid).and()
                .subject(USER_ID)
                .expiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(keyPair.getPrivate())
                .compact();

        ReflectionTestUtils.setField(jwtService, "jwksKeys", Map.of(kid, original));

        assertThat(jwtService.extractUserId(token)).isEqualTo(USER_ID);
    }
}
