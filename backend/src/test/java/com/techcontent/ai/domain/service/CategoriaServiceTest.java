package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.repository.CategoriaRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class CategoriaServiceTest {

    @Mock
    private CategoriaRepository categoriaRepository;

    @InjectMocks
    private CategoriaService categoriaService;

    @Test
    @DisplayName("Debería retornar la lista de categorías con su conteo para un usuario específico")
    void deberiaListarCategoriasConConteoPorUsuario() {
        // Arrange
        UUID userId = UUID.randomUUID();
        List<CategoriaResponse> respuestaEsperada = List.of(
                new CategoriaResponse("Leyes", 5L),
                new CategoriaResponse("Salud", 2L)
        );

        when(categoriaRepository.findCategoriasConConteoByUserId(userId))
                .thenReturn(respuestaEsperada);

        // Act
        List<CategoriaResponse> resultado = categoriaService.listarConConteo(userId);

        // Assert
        assertThat(resultado).isNotNull();
        assertThat(resultado).hasSize(2);
        assertThat(resultado.get(0).nombre()).isEqualTo("Leyes");
        assertThat(resultado.get(0).totalConsultas()).isEqualTo(5L);
        assertThat(resultado.get(1).totalConsultas()).isEqualTo(2L);

        verify(categoriaRepository).findCategoriasConConteoByUserId(userId);
    }

    @Test
    @DisplayName("Debería retornar una lista vacía cuando el usuario no tiene contenidos registrados")
    void deberiaRetornarListaVaciaCuandoUsuarioNoTieneContenidos() {
        // Arrange
        UUID userId = UUID.randomUUID();

        when(categoriaRepository.findCategoriasConConteoByUserId(userId))
                .thenReturn(List.of());

        // Act
        List<CategoriaResponse> resultado = categoriaService.listarConConteo(userId);

        // Assert
        assertThat(resultado).isEmpty();
        verify(categoriaRepository).findCategoriasConConteoByUserId(userId);
    }
}