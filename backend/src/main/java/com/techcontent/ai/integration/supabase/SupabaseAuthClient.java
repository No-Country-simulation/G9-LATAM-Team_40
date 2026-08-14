package com.techcontent.ai.integration.supabase;

import com.techcontent.ai.api.exception.InvalidCredentialsException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
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
            return restClient.post()
                    .uri("/auth/v1/signup")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(SupabaseAuthResponse.class);
        } catch (HttpClientErrorException e) {
            log.warn("Error en registro ({}): {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new IllegalArgumentException("Email ya registrado o datos invalidos.");
        }
    }

    public SupabaseAuthResponse signIn(SupabaseAuthRequest request) {
        try {
            return restClient.post()
                    .uri("/auth/v1/token?grant_type=password")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(SupabaseAuthResponse.class);
        } catch (HttpClientErrorException e) {
            log.warn("Autenticacion fallida ({}): {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new InvalidCredentialsException("Credenciales incorrectas.");
        }
    }
}
