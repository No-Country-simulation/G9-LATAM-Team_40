package com.techcontent.ai.integration.supabase;

import com.techcontent.ai.api.exception.AuthProviderException;
import com.techcontent.ai.api.exception.InvalidCredentialsException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

@Slf4j
@Component
public class SupabaseAuthClient {

    private final RestClient restClient;

    public SupabaseAuthClient(RestClient.Builder builder,
                               @Value("${supabase.auth.url}") String authUrl,
                               @Value("${supabase.anon.key}") String anonKey) {
        this.restClient = builder
                .baseUrl(authUrl)
                .defaultHeader("apikey", anonKey)
                .defaultHeader("Authorization", "Bearer " + anonKey)
                .build();
    }

    public SupabaseAuthResponse signUp(SupabaseAuthRequest request) {
        try {
            SupabaseAuthResponse response = restClient.post()
                    .uri("/signup")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(SupabaseAuthResponse.class);
            return requireSession(response, "No se pudo completar el registro. Revisa el correo o intenta de nuevo.");
        } catch (HttpClientErrorException e) {
            log.warn("Error en registro ({}): {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new IllegalArgumentException("Email ya registrado o datos invalidos.");
        } catch (ResourceAccessException e) {
            log.error("No se pudo contactar Supabase Auth en registro: {}", e.getMessage());
            throw new AuthProviderException("No se pudo contactar el servicio de autenticación.");
        }
    }

    public SupabaseAuthResponse signIn(SupabaseAuthRequest request) {
        try {
            SupabaseAuthResponse response = restClient.post()
                    .uri("/token?grant_type=password")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(SupabaseAuthResponse.class);
            return requireSession(response, "Credenciales incorrectas.");
        } catch (HttpClientErrorException e) {
            log.warn("Autenticacion fallida ({}): {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new InvalidCredentialsException("Credenciales incorrectas.");
        } catch (ResourceAccessException e) {
            log.error("No se pudo contactar Supabase Auth en login: {}", e.getMessage());
            throw new AuthProviderException("No se pudo contactar el servicio de autenticación.");
        }
    }

    private static SupabaseAuthResponse requireSession(SupabaseAuthResponse response, String missingTokenMessage) {
        if (response == null || response.accessToken() == null || response.accessToken().isBlank()) {
            throw new IllegalArgumentException(missingTokenMessage);
        }
        return response;
    }
}
