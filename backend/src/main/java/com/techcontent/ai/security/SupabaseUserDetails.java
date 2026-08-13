package com.techcontent.ai.security;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.List;
import java.util.UUID;

public class SupabaseUserDetails implements UserDetails {

    private final UUID userId;
    private final String email;
    private final String role;

    public SupabaseUserDetails(UUID userId, String email, String role) {
        this.userId = userId;
        this.email = email;
        this.role = role;
    }

    

    public UUID getUserId() {
        return userId;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
       String effectiveRole = role == null || role.isBlank()
            ? "authenticated"
            : role;

        String authority = effectiveRole.startsWith("ROLE_")
            ? effectiveRole
            : "ROLE_" + effectiveRole.toUpperCase();

        return List.of(new SimpleGrantedAuthority(authority));
    }

    @Override
    public String getPassword() {
        return null;
    }

    @Override
    public String getUsername() {
        return email;
    }

   
    public String getRole() {
        return role;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return true;
    }
}
