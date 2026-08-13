package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.api.exception.ArchivoNotFoundException;
import com.techcontent.ai.domain.model.Archivo;
import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ArchivoServiceTest {

    @Mock
    private ArchivoRepository archivoRepository;

    @Mock
    private OciStorageClient ociStorageClient;

    @InjectMocks
    private ArchivoService service;

    private static final UUID USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");
    private static final UUID ARCHIVO_ID = UUID.fromString("00000000-0000-0000-0000-000000000002");

    @org.junit.jupiter.api.BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(service, "filesBucket", "test-bucket");
    }

    private Archivo archivoGuardado() {
        return Archivo.builder()
                .id(ARCHIVO_ID)
                .userId(USER_ID)
                .nombre("documento.pdf")
                .url("https://oci/test-bucket/documento.pdf")
                .tamano(1024L)
                .tipo("application/pdf")
                .subidoEn(LocalDateTime.now())
                .build();
    }

    @Test
    void subir_archivoValido_deberiaSubirYPersistir() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "documento.pdf", "application/pdf", "contenido pdf".getBytes()
        );

        when(ociStorageClient.upload(anyString(), anyString(), any(), anyString()))
                .thenReturn("https://oci/test-bucket/documento.pdf");
        when(archivoRepository.save(any(Archivo.class))).thenReturn(archivoGuardado());

        ArchivoResponse response = service.subir(file, USER_ID);

        assertThat(response.nombre()).isEqualTo("documento.pdf");
        assertThat(response.tipo()).isEqualTo("application/pdf");
        verify(ociStorageClient).upload(eq("test-bucket"), anyString(), any(), eq("application/pdf"));
        verify(archivoRepository).save(any(Archivo.class));
    }

    @Test
    void subir_tipoDeArchivoNoPermitido_deberiaLanzarIllegalArgument() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "imagen.png", "image/png", "datos".getBytes()
        );

        assertThatThrownBy(() -> service.subir(file, USER_ID))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Tipo de archivo no permitido");

        verifyNoInteractions(ociStorageClient, archivoRepository);
    }

    @Test
    void subir_archivoVacio_deberiaLanzarIllegalArgument() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "vacio.pdf", "application/pdf", new byte[0]
        );

        assertThatThrownBy(() -> service.subir(file, USER_ID))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("vacio");
    }

    @Test
    void subir_archivoDemasiadoGrande_deberiaLanzarIllegalArgument() {
        byte[] datosGrandes = new byte[11 * 1024 * 1024]; // 11 MB
        MockMultipartFile file = new MockMultipartFile(
                "file", "grande.pdf", "application/pdf", datosGrandes
        );

        assertThatThrownBy(() -> service.subir(file, USER_ID))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("tamano maximo");
    }

    @Test
    void listar_deberiaRetornarTodosLosArchivosDelUsuario() {
        when(archivoRepository.findByUserId(USER_ID)).thenReturn(List.of(archivoGuardado()));

        List<ArchivoResponse> responses = service.listar(USER_ID);

        assertThat(responses).hasSize(1);
        assertThat(responses.get(0).nombre()).isEqualTo("documento.pdf");
        verify(archivoRepository).findByUserId(USER_ID);
    }

    @Test
    void obtenerPorId_existente_deberiaRetornarElArchivo() {
        when(archivoRepository.findByIdAndUserId(ARCHIVO_ID, USER_ID))
                .thenReturn(Optional.of(archivoGuardado()));

        ArchivoResponse response = service.obtenerPorId(ARCHIVO_ID, USER_ID);

        assertThat(response.id()).isEqualTo(ARCHIVO_ID.toString());
        verify(archivoRepository).findByIdAndUserId(ARCHIVO_ID, USER_ID);
    }

    @Test
    void obtenerPorId_noExistente_deberiaLanzarArchivoNotFound() {
        when(archivoRepository.findByIdAndUserId(ARCHIVO_ID, USER_ID)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.obtenerPorId(ARCHIVO_ID, USER_ID))
                .isInstanceOf(ArchivoNotFoundException.class);
    }
}
