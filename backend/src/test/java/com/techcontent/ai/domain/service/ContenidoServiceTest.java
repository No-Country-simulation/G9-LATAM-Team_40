package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.request.ContenidoLoteRequest;
import com.techcontent.ai.api.dto.request.ContenidoRequest;
import com.techcontent.ai.api.dto.response.ContenidoResponse;
import com.techcontent.ai.domain.model.Contenido;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import com.techcontent.ai.domain.service.ContenidoService;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.ml.MlResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ContenidoServiceTest {

    @Mock
    private ContenidoRepository repository;

    @Mock
    private MlClient mlClient;

    @InjectMocks
    private ContenidoService contenidoService;

    private UUID userId;

    @BeforeEach
    void setUp() {
        userId = UUID.randomUUID();
    }

    @Test
    void clasificar_deberiaLlamarAlMlClientYGuardarElContenido() {
        ContenidoRequest request = new ContenidoRequest("Titulo de prueba", "Texto suficientemente largo para pasar validacion");

        MlResponse mlResponseSimulado = new MlResponse(
                "Backend",
                0.92,
                List.of("java", "spring")
        );

        when(mlClient.predict(anyString())).thenReturn(mlResponseSimulado);

        when(repository.save(any(Contenido.class))).thenAnswer(invocation -> {
            Contenido c = invocation.getArgument(0);
            c.setId(UUID.randomUUID());
            return c;
        });

        ContenidoResponse response = contenidoService.clasificar(request, userId);

        assertNotNull(response);
        assertEquals("Backend", response.categoria());
        assertEquals(0.92, response.probabilidad());
        assertEquals(List.of("java", "spring"), response.palabrasClave());

        verify(mlClient, times(1)).predict(request.texto());
        verify(repository, times(1)).save(any(Contenido.class));
    }

    @Test
    void procesarLote_deberiaClasificarCadaItemDeLaLista() {
       
        ContenidoRequest item1 = new ContenidoRequest("Titulo 1", "Texto suficientemente largo numero uno aqui");
        ContenidoRequest item2 = new ContenidoRequest("Titulo 2", "Texto suficientemente largo numero dos aqui");
        ContenidoLoteRequest lote = new ContenidoLoteRequest(List.of(item1, item2));

        MlResponse mlResponseSimulado = new MlResponse("Frontend", 0.80, List.of("react"));
        when(mlClient.predict(anyString())).thenReturn(mlResponseSimulado);
        when(repository.save(any(Contenido.class))).thenAnswer(invocation -> {
            Contenido c = invocation.getArgument(0);
            c.setId(UUID.randomUUID());
            return c;
        });

       
        List<ContenidoResponse> resultados = contenidoService.procesarLote(lote, userId);

        assertEquals(2, resultados.size());
        verify(mlClient, times(2)).predict(anyString());
        verify(repository, times(2)).save(any(Contenido.class));
    }

    @Test
    void buscar_deberiaDelegarEnElRepositorioConLosParametrosCorrectos() {
        
        String query = "spring";
        Contenido contenidoEncontrado = Contenido.builder()
                .id(UUID.randomUUID())
                .userId(userId)
                .titulo("Encontrado")
                .texto("Texto de ejemplo")
                .categoria("Backend")
                .probabilidad(0.75)
                .palabrasClave(List.of("spring"))
                .procesadoEn(LocalDateTime.now())
                .build();

        when(repository.buscarPorKeyword(query, userId)).thenReturn(List.of(contenidoEncontrado));

        
        List<ContenidoResponse> resultados = contenidoService.buscar(query, userId);

        assertEquals(1, resultados.size());
        assertEquals("Backend", resultados.get(0).categoria());
        verify(repository, times(1)).buscarPorKeyword(query, userId);
    }

    @Test
    void buscar_siNoHayResultados_deberiaRetornarListaVacia() {
        when(repository.buscarPorKeyword(anyString(), any(UUID.class))).thenReturn(List.of());

        List<ContenidoResponse> resultados = contenidoService.buscar("inexistente", userId);

        assertNotNull(resultados);
        assertTrue(resultados.isEmpty());
    }

    @Test
    void listarPorUsuario_deberiaDelegarEnElRepositorio() {
        Contenido contenido = Contenido.builder()
                .id(UUID.randomUUID())
                .userId(userId)
                .titulo("Mi contenido")
                .texto("Texto")
                .categoria("QA")
                .probabilidad(0.5)
                .palabrasClave(List.of())
                .procesadoEn(LocalDateTime.now())
                .build();

        when(repository.findByUserId(userId)).thenReturn(List.of(contenido));

        List<ContenidoResponse> resultados = contenidoService.listarPorUsuario(userId);

        assertEquals(1, resultados.size());
        verify(repository, times(1)).findByUserId(userId);
    }
}