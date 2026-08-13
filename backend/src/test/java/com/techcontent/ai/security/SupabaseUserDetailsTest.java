package com.techcontent.ai.security;

import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class SupabaseUserDetailsTest {

    @Test
    void userDetails_conRolAutenticado_retornaDatosYEstadoActivo() {
        UUID userId = UUID.randomUUID();

        SupabaseUserDetails user = new SupabaseUserDetails(
                userId,
                "usuario@example.com",
                "authenticated"
        );

        assertEquals(userId, user.getUserId());
        assertEquals("usuario@example.com", user.getUsername());
        assertEquals("authenticated", user.getRole());
        assertNull(user.getPassword());
        assertEquals(
                "ROLE_AUTHENTICATED",
                user.getAuthorities().iterator().next().getAuthority()
        );
        assertTrue(user.isAccountNonExpired());
        assertTrue(user.isAccountNonLocked());
        assertTrue(user.isCredentialsNonExpired());
        assertTrue(user.isEnabled());
    }

    @Test
    void getAuthorities_conRolNulo_utilizaAuthenticated() {
        SupabaseUserDetails user = new SupabaseUserDetails(
                UUID.randomUUID(),
                "usuario@example.com",
                null
        );

        assertEquals(
                "ROLE_AUTHENTICATED",
                user.getAuthorities().iterator().next().getAuthority()
        );
    }

    @Test
    void getAuthorities_conPrefijoRole_noDuplicaPrefijo() {
        SupabaseUserDetails user = new SupabaseUserDetails(
                UUID.randomUUID(),
                "admin@example.com",
                "ROLE_ADMIN"
        );

        assertEquals(
                "ROLE_ADMIN",
                user.getAuthorities().iterator().next().getAuthority()
        );
    }
}