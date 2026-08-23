package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.api.dto.response.PaginaResponse;
import com.techcontent.ai.api.exception.ArchivoNotFoundException;
import com.techcontent.ai.domain.model.Archivo;
import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
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
    private static final UUID OTRO_USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000003");
    private static final UUID ARCHIVO_ID = UUID.fromString("00000000-0000-0000-0000-000000000002");

    @BeforeEach
    void setUp() {
        // Se inyectan las propiedades @Value actualizadas en el servicio
        ReflectionTestUtils.setField(service, "datasetBucket", "test-bucket");
        ReflectionTestUtils.setField(service, "ociPrefix", "prod");
    }

    private Archivo archivoGuardado() {
        return Archivo.builder()
                .id(ARCHIVO_ID)
                .userId(USER_ID)
                .nombre("documento.pdf")
                .url("https://oci/o/prod/archivos/LEYES/pdf/documento.pdf")
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

        when(ociStorageClient.upload(anyString(), anyString(), any(), anyLong(), anyString()))
                .thenReturn("https://oci/o/prod/archivos/LEYES/pdf/documento.pdf");
        when(archivoRepository.save(any(Archivo.class))).thenReturn(archivoGuardado());

        ArchivoResponse response = service.subir(file, USER_ID, null);

        assertThat(response.nombre()).isEqualTo("documento.pdf");
        assertThat(response.tipo()).isEqualTo("application/pdf");
        verify(ociStorageClient).upload(eq("test-bucket"), eq("prod/archivos/LEYES/pdf/documento.pdf"), any(), anyLong(), eq("application/pdf"));
        verify(archivoRepository).save(any(Archivo.class));
    }

    @Test
    void subir_conCategoriaExplicitaiso_deberiaGuardarEnSubcarpetaIsos() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "manual.pdf", "application/pdf", "contenido".getBytes()
        );

        when(ociStorageClient.upload(anyString(), anyString(), any(), anyLong(), anyString()))
                .thenReturn("https://oci/o/prod/archivos/ISOS/pdf/manual.pdf");
        when(archivoRepository.save(any(Archivo.class))).thenReturn(archivoGuardado());

        service.subir(file, USER_ID, "ISO");

        verify(ociStorageClient).upload(
                eq("test-bucket"),
                eq("prod/archivos/ISOS/pdf/manual.pdf"),
                any(),
                anyLong(),
                eq("application/pdf")
        );
    }

    @Test
    void subir_tipoDeArchivoNoPermitido_deberiaLanzarIllegalArgument() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "imagen.png", "image/png", "datos".getBytes()
        );

        assertThatThrownBy(() -> service.subir(file, USER_ID, null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Tipo de archivo no permitido");

        verifyNoInteractions(ociStorageClient, archivoRepository);
    }

    @Test
    void subir_archivoVacio_deberiaLanzarIllegalArgument() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "vacio.pdf", "application/pdf", new byte[0]
        );

        assertThatThrownBy(() -> service.subir(file, USER_ID, null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("vacio");
    }

    @Test
    void subir_archivoDemasiadoGrande_deberiaLanzarIllegalArgument() {
        byte[] datosGrandes = new byte[11 * 1024 * 1024]; // 11 MB
        MockMultipartFile file = new MockMultipartFile(
                "file", "grande.pdf", "application/pdf", datosGrandes
        );

        assertThatThrownBy(() -> service.subir(file, USER_ID, null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("tamano maximo");
    }

    @Test
    void listar_conPaginacion_deberiaRetornarPaginaDelUsuario() {
        when(archivoRepository.buscarPorUsuario(
                eq(USER_ID), eq(""), eq(""), any(Pageable.class)))
                .thenReturn(new PageImpl<>(
                        List.of(archivoGuardado()),
                        PageRequest.of(0, 20, Sort.by(Sort.Direction.DESC, "subidoEn")),
                        1
                ));

        PaginaResponse<ArchivoResponse> response = service.listar(USER_ID, 0, 20, null, null);

        assertThat(response.items()).hasSize(1);
        assertThat(response.items().get(0).nombre()).isEqualTo("documento.pdf");
        assertThat(response.page()).isZero();
        assertThat(response.size()).isEqualTo(20);
        assertThat(response.totalElements()).isEqualTo(1);
        assertThat(response.totalPages()).isEqualTo(1);
        verify(archivoRepository).buscarPorUsuario(
                eq(USER_ID), eq(""), eq(""), argThat(pageable ->
                        pageable.getPageNumber() == 0
                                && pageable.getPageSize() == 20
                                && pageable.getSort().getOrderFor("subidoEn") != null
                                && pageable.getSort().getOrderFor("subidoEn").isDescending()
                ));
    }

    @Test
    void listar_conBusqueda_deberiaNormalizarYFiltrarPorNombre() {
        when(archivoRepository.buscarPorUsuario(
                eq(USER_ID), eq("DOC"), eq(""), any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(archivoGuardado())));

        PaginaResponse<ArchivoResponse> response = service.listar(USER_ID, 0, 20, "  DOC  ", "");

        assertThat(response.items()).hasSize(1);
        assertThat(response.items().get(0).nombre()).isEqualTo("documento.pdf");
        verify(archivoRepository).buscarPorUsuario(
                eq(USER_ID), eq("DOC"), eq(""), any(Pageable.class));
    }

    @Test
    void listar_conBusquedaYTipo_deberiaNormalizarYFiltrar() {
        when(archivoRepository.buscarPorUsuario(
                eq(USER_ID), eq("manual"), eq("application/pdf"), any(Pageable.class)))
                .thenReturn(new PageImpl<>(List.of(archivoGuardado())));

        PaginaResponse<ArchivoResponse> response = service.listar(
                USER_ID, 0, 20, "  manual  ", " PDF "
        );

        assertThat(response.items()).hasSize(1);
        verify(archivoRepository).buscarPorUsuario(
                eq(USER_ID), eq("manual"), eq("application/pdf"), any(Pageable.class));
    }

    @Test
    void listar_conTipoNoPermitido_deberiaLanzarIllegalArgument() {
        assertThatThrownBy(() -> service.listar(USER_ID, 0, 20, "", "xlsx"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("pdf, txt, md");

        verifyNoInteractions(archivoRepository);
    }

    @Test
    void listar_conPaginaNegativa_deberiaLanzarIllegalArgument() {
        assertThatThrownBy(() -> service.listar(USER_ID, -1, 20, "", ""))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("pagina");

        verifyNoInteractions(archivoRepository);
    }

    @Test
    void listar_conTamanoFueraDeRango_deberiaLanzarIllegalArgument() {
        assertThatThrownBy(() -> service.listar(USER_ID, 0, 101, "", ""))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("entre 1 y 100");

        verifyNoInteractions(archivoRepository);
    }

    @Test
    void listar_conBusquedaDemasiadoLarga_deberiaLanzarIllegalArgument() {
        assertThatThrownBy(() -> service.listar(USER_ID, 0, 20, "a".repeat(101), ""))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("100 caracteres");

        verifyNoInteractions(archivoRepository);
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

    @Test
    void eliminar_existente_deberiaEliminarEnOciYPersistencia() {
        Archivo archivo = archivoGuardado();
        when(archivoRepository.findByIdAndUserId(ARCHIVO_ID, USER_ID))
                .thenReturn(Optional.of(archivo));
        service.eliminar(ARCHIVO_ID, USER_ID);

        verify(archivoRepository).findByIdAndUserId(ARCHIVO_ID, USER_ID);
        verify(ociStorageClient).delete(eq("test-bucket"), eq("prod/archivos/LEYES/pdf/documento.pdf"));
        verify(archivoRepository).delete(archivo);
    }

    @Test
    void eliminar_noExistente_deberiaLanzarArchivoNotFound() {
        when(archivoRepository.findByIdAndUserId(ARCHIVO_ID, USER_ID))
                .thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.eliminar(ARCHIVO_ID, USER_ID))
                .isInstanceOf(ArchivoNotFoundException.class);

        verifyNoInteractions(ociStorageClient);
        verify(archivoRepository, never()).delete(any(Archivo.class));
    }

    @Test
    void eliminar_archivoDeOtroUsuario_deberiaTratarloComoNoEncontrado() {
        when(archivoRepository.findByIdAndUserId(ARCHIVO_ID, OTRO_USER_ID))
                .thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.eliminar(ARCHIVO_ID, OTRO_USER_ID))
                .isInstanceOf(ArchivoNotFoundException.class);

        verify(archivoRepository).findByIdAndUserId(ARCHIVO_ID, OTRO_USER_ID);
        verifyNoInteractions(ociStorageClient);
        verify(archivoRepository, never()).delete(any(Archivo.class));
    }

    @Test
    void eliminar_cuandoOciFalla_noDeberiaEliminarDePersistencia() {
        Archivo archivo = archivoGuardado();
        when(archivoRepository.findByIdAndUserId(ARCHIVO_ID, USER_ID))
                .thenReturn(Optional.of(archivo));
        doThrow(new RuntimeException("Error en eliminación desde OCI"))
                .when(ociStorageClient).delete("test-bucket", "prod/archivos/LEYES/pdf/documento.pdf");

        assertThatThrownBy(() -> service.eliminar(ARCHIVO_ID, USER_ID))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Error en eliminación desde OCI");

        verify(archivoRepository).findByIdAndUserId(ARCHIVO_ID, USER_ID);
        verify(ociStorageClient).delete("test-bucket", "prod/archivos/LEYES/pdf/documento.pdf");
        verify(archivoRepository, never()).delete(any(Archivo.class));
    }
}