package com.techcontent.ai.api.controller;

import com.techcontent.ai.integration.supabase.SupabaseAuthClient;
import com.techcontent.ai.integration.supabase.SupabaseAuthRequest;
import com.techcontent.ai.integration.supabase.SupabaseAuthResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final SupabaseAuthClient supabaseAuthClient;

    @PostMapping("/register")
    public ResponseEntity<SupabaseAuthResponse> register(@RequestBody SupabaseAuthRequest request) {
        return ResponseEntity.ok(supabaseAuthClient.signUp(request));
    }

    @PostMapping("/login")
    public ResponseEntity<SupabaseAuthResponse> login(@RequestBody SupabaseAuthRequest request) {
        return ResponseEntity.ok(supabaseAuthClient.signIn(request));
    }
}
