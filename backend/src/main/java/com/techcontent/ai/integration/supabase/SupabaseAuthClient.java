package com.techcontent.ai.integration.supabase;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class SupabaseAuthClient {

    private final RestClient restClient;

    public SupabaseAuthClient(
            @Value("${supabase.auth.url}") String authUrl,
            @Value("${supabase.anon.key}") String anonKey) {
        this.restClient = RestClient.builder()
                .baseUrl(authUrl)
                .defaultHeader("apikey", anonKey)
                .build();
    }

    public SupabaseAuthResponse signUp(SupabaseAuthRequest request) {
        return restClient.post()
                .uri("/signup")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(SupabaseAuthResponse.class);
    }

    public SupabaseAuthResponse signIn(SupabaseAuthRequest request) {
        return restClient.post()
                .uri("/token?grant_type=password")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(SupabaseAuthResponse.class);
    }
}
