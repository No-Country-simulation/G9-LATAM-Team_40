package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.ArchivoResponse;
import com.techcontent.ai.domain.model.Archivo;
import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.integration.oci.OciStorageClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.ByteArrayInputStream;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ArchivoServiceTest {

    @Mock private ArchivoRepository repository;
    @Mock private OciStorageClient storage;
    @Mock private IndiceUsuarioService indice;
    @InjectMocks private ArchivoService service;

    private static final UUID USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");
    private static final UUID FILE_ID = UUID.fromString("00000000-0000-0000-0000-000000000002");

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(service, "datasetBucket", "dataset");
        ReflectionTestUtils.setField(service, "ociPrefix", "prod");
    }

    @Test
    void subir_guardaRutaPorUsuarioYNoExponeUrl() {
        MockMultipartFile file = new MockMultipartFile("file", "Manual ACME.md", "text/markdown", "# ACME".getBytes());
        when(storage.upload(anyString(), anyString(), any(), any(Long.class), anyString())).thenReturn("oci://dataset/internal");
        when(repository.save(any(Archivo.class))).thenAnswer(invocation -> invocation.getArgument(0));

        ArchivoResponse response = service.subir(file, USER_ID, "LEYES");

        ArgumentCaptor<String> objectName = ArgumentCaptor.forClass(String.class);
        verify(storage).upload(anyString(), objectName.capture(), any(), any(Long.class), anyString());
        assertThat(objectName.getValue()).startsWith("prod/users/" + USER_ID + "/input/LEYES/");
        assertThat(response).extracting(ArchivoResponse::nombre, ArchivoResponse::dominio).containsExactly("Manual ACME.md", "LEYES");
        verify(indice).marcarSucio(USER_ID);
    }

    @Test
    void subir_rechazaPathTraversal() {
        MockMultipartFile file = new MockMultipartFile("file", "../secreto.pdf", "application/pdf", "data".getBytes());
        assertThatThrownBy(() -> service.subir(file, USER_ID, "ISOS"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("seguro");
    }

    @Test
    void eliminar_marcaPendienteYEnsuciaIndice() {
        Archivo file = Archivo.builder().id(FILE_ID).userId(USER_ID).nombre("a.pdf").url("oci://dataset/x")
                .objectName("prod/users/" + USER_ID + "/input/ISOS/id.pdf")
                .tamano(4L).tipo("application/pdf").subidoEn(LocalDateTime.now()).build();
        when(repository.findByIdAndUserId(FILE_ID, USER_ID)).thenReturn(Optional.of(file));
        when(repository.save(any(Archivo.class))).thenAnswer(invocation -> invocation.getArgument(0));

        service.eliminar(FILE_ID, USER_ID);

        assertThat(file.isPendienteEliminacion()).isTrue();
        verify(indice).marcarSucio(USER_ID);
    }

    @Test
    void descargar_compruebaOwnershipYDevuelveStream() {
        Archivo file = Archivo.builder().id(FILE_ID).userId(USER_ID).nombre("a.pdf").url("oci://dataset/x")
                .objectName("prod/users/" + USER_ID + "/input/ISOS/id.pdf")
                .tamano(4L).tipo("application/pdf").build();
        when(repository.findByIdAndUserId(FILE_ID, USER_ID)).thenReturn(Optional.of(file));
        when(storage.download("dataset", file.getObjectName())).thenReturn(new ByteArrayInputStream("data".getBytes()));

        ArchivoDownload download = service.descargar(FILE_ID, USER_ID);

        assertThat(download.nombre()).isEqualTo("a.pdf");
        assertThat(download.tamano()).isEqualTo(4L);
    }
}
