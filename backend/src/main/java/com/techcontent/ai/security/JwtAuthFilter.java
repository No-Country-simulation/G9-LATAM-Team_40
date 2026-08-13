package com.techcontent.ai.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

@Component
@RequiredArgsConstructor
public class JwtAuthFilter extends OncePerRequestFilter {

    static final String JWT_ERROR_ATTRIBUTE = "JWT_ERROR_TYPE";

    private final JwtService jwtService;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {

        String authHeader = request.getHeader("Authorization");

        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            chain.doFilter(request, response);
            return;
        }

        String token = authHeader.substring(7);
        JwtService.TokenValidationResult result = jwtService.validateToken(token);

        if (result == JwtService.TokenValidationResult.EXPIRED) {
            request.setAttribute(JWT_ERROR_ATTRIBUTE, "EXPIRED");
        } else if (result == JwtService.TokenValidationResult.INVALID) {
            request.setAttribute(JWT_ERROR_ATTRIBUTE, "INVALID");
        }

        if (result == JwtService.TokenValidationResult.VALID
                && SecurityContextHolder.getContext().getAuthentication() == null) {
            UUID userId = UUID.fromString(jwtService.extractUserId(token));
            String email = jwtService.extractEmail(token);

            SupabaseUserDetails userDetails = new SupabaseUserDetails(userId, email);
            UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                    userDetails, null, userDetails.getAuthorities()
            );
            auth.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
            SecurityContextHolder.getContext().setAuthentication(auth);
        }

        chain.doFilter(request, response);
    }
}
