package com.techcontent.ai.security;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.JwtParserBuilder;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.math.BigInteger;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.security.AlgorithmParameters;
import java.security.Key;
import java.security.KeyFactory;
import java.security.PublicKey;
import java.security.spec.ECGenParameterSpec;
import java.security.spec.ECParameterSpec;
import java.security.spec.ECPoint;
import java.security.spec.ECPublicKeySpec;
import java.util.Base64;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
public class JwtService {

    public enum TokenValidationResult {
        VALID, EXPIRED, INVALID
    }

    private final SecretKey secretKey;
    private final Map<String, PublicKey> jwksKeys = new ConcurrentHashMap<>();
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${supabase.jwks.url:}")
    private String jwksUrl;

    public JwtService(@Value("${supabase.jwt.secret:}") String secret) {
        if (secret == null || secret.isBlank()) {
            log.warn("SUPABASE_JWT_SECRET no configurado. Validacion HS256 sera rechazada.");
            this.secretKey = null;
        } else {
            this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        }
    }

    @PostConstruct
    void loadJwks() {
        if (jwksUrl == null || jwksUrl.isBlank()) {
            log.info("supabase.jwks.url no configurada. Solo se validaran tokens HS256.");
            return;
        }
        try {
            byte[] bytes = URI.create(jwksUrl).toURL().openStream().readAllBytes();
            JsonNode root = objectMapper.readTree(bytes);
            JsonNode keys = root.get("keys");
            if (keys == null || !keys.isArray()) {
                log.warn("Respuesta JWKS sin campo 'keys' valido en {}", jwksUrl);
                return;
            }
            for (JsonNode key : keys) {
                String kty = key.path("kty").asText();
                String kid = key.path("kid").asText();
                String alg = key.path("alg").asText();
                if ("EC".equals(kty) && "ES256".equals(alg)) {
                    String x = key.path("x").asText();
                    String y = key.path("y").asText();
                    PublicKey publicKey = buildEcPublicKey(x, y);
                    jwksKeys.put(kid, publicKey);
                    log.info("Clave JWKS cargada: kid={}, alg={}", kid, alg);
                }
            }
            log.info("JWKS cargadas: {} clave(s) EC desde {}", jwksKeys.size(), jwksUrl);
        } catch (Exception e) {
            log.error("No se pudieron cargar las JWKS desde {}: {}", jwksUrl, e.getMessage());
        }
    }

    PublicKey buildEcPublicKey(String xB64, String yB64) throws Exception {
        Base64.Decoder decoder = Base64.getUrlDecoder();
        BigInteger x = new BigInteger(1, decoder.decode(xB64));
        BigInteger y = new BigInteger(1, decoder.decode(yB64));

        AlgorithmParameters params = AlgorithmParameters.getInstance("EC");
        params.init(new ECGenParameterSpec("secp256r1"));
        ECParameterSpec ecParams = params.getParameterSpec(ECParameterSpec.class);

        ECPublicKeySpec keySpec = new ECPublicKeySpec(new ECPoint(x, y), ecParams);
        return KeyFactory.getInstance("EC").generatePublic(keySpec);
    }

    private String extractHeaderClaim(String token, String claimName) {
        try {
            String[] parts = token.split("\\.");
            if (parts.length < 2) return null;
            byte[] headerBytes = Base64.getUrlDecoder().decode(parts[0]);
            return objectMapper.readTree(headerBytes).path(claimName).asText(null);
        } catch (Exception e) {
            return null;
        }
    }

    private Key resolveKey(String token) {
        String alg = extractHeaderClaim(token, "alg");
        if ("ES256".equals(alg)) {
            String kid = extractHeaderClaim(token, "kid");
            if (kid != null && jwksKeys.containsKey(kid)) {
                return jwksKeys.get(kid);
            }
            if (!jwksKeys.isEmpty()) {
                return jwksKeys.values().iterator().next();
            }
            throw new IllegalStateException("No hay claves JWKS disponibles para ES256");
        }
        // Ruta HS256 (default)
        if (secretKey == null) throw new IllegalStateException("JWT secret no configurado");
        return secretKey;
    }

    public TokenValidationResult validateToken(String token) {
        try {
            extractClaims(token);
            return TokenValidationResult.VALID;
        } catch (ExpiredJwtException e) {
            return TokenValidationResult.EXPIRED;
        } catch (JwtException | IllegalArgumentException | IllegalStateException e) {
            return TokenValidationResult.INVALID;
        }
    }

    public boolean isTokenValid(String token) {
        return validateToken(token) == TokenValidationResult.VALID;
    }

    public Claims extractClaims(String token) {
        Key key = resolveKey(token);
        JwtParserBuilder builder = Jwts.parser();
        if (key instanceof PublicKey pk) {
            builder.verifyWith(pk);
        } else {
            builder.verifyWith((SecretKey) key);
        }
        return builder.build().parseSignedClaims(token).getPayload();
    }

    public String extractUserId(String token) {
        return extractClaims(token).getSubject();
    }

    public String extractEmail(String token) {
        return extractClaims(token).get("email", String.class);
    }

    public String extractRole(String token) {
        return extractClaims(token).get("role", String.class);
    }
}
