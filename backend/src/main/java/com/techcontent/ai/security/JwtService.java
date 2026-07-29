package com.techcontent.ai.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;

@Slf4j
@Service
public class JwtService {

    private final SecretKey secretKey;

    public JwtService(@Value("${supabase.jwt.secret}") String secret) {
        if (secret == null || secret.isBlank()) {
            log.warn("SUPABASE_JWT_SECRET no configurado. Toda validacion JWT sera rechazada hasta recibir el secreto real.");
            this.secretKey = null;
        } else {
            this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        }
    }

    public Claims extractClaims(String token) {
        if (secretKey == null) throw new IllegalStateException("JWT secret no configurado");
        return Jwts.parser()
                .verifyWith(secretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public boolean isTokenValid(String token) {
        if (secretKey == null) return false;
        try {
            extractClaims(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    public String extractUserId(String token) {
        return extractClaims(token).getSubject();
    }

    public String extractEmail(String token) {
        return extractClaims(token).get("email", String.class);
    }
}
