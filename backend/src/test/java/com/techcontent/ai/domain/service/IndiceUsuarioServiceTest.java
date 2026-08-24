package com.techcontent.ai.domain.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.techcontent.ai.domain.model.Archivo;
import com.techcontent.ai.domain.model.IndiceEstado;
import com.techcontent.ai.domain.model.IndiceUsuario;
import com.techcontent.ai.domain.repository.ArchivoRepository;
import com.techcontent.ai.domain.repository.IndiceUsuarioRepository;
import com.techcontent.ai.integration.ml.IndexJobRequest;
import com.techcontent.ai.integration.ml.IndexJobResponse;
import com.techcontent.ai.integration.ml.MlClient;
import com.techcontent.ai.integration.oci.OciStorageClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class IndiceUsuarioServiceTest {

    @Mock private IndiceUsuarioRepository indiceRepository;
    @Mock private ArchivoRepository archivoRepository;
    @Mock private MlClient mlClient;
    @Mock private OciStorageClient storage;

    private IndiceUsuarioService service;
    private static final UUID USER_ID = UUID.fromString("00000000-0000-0000-0000-000000000001");

    @BeforeEach
    void setUp() {
        service = new IndiceUsuarioService(indiceRepository, archivoRepository, mlClient, storage, new ObjectMapper());
        ReflectionTestUtils.setField(service, "datasetBucket", "dataset");
    }

    @Test
    void marcarSucio_incrementaGeneracionYMarcaDirty() {
        IndiceUsuario index = IndiceUsuario.builder().userId(USER_ID).estado(IndiceEstado.IDLE).requestedGeneration(2).build();
        when(indiceRepository.findById(USER_ID)).thenReturn(Optional.of(index));
        when(indiceRepository.save(any(IndiceUsuario.class))).thenAnswer(invocation -> invocation.getArgument(0));

        service.marcarSucio(USER_ID);

        assertThat(index.getRequestedGeneration()).isEqualTo(3);
        assertThat(index.getEstado()).isEqualTo(IndiceEstado.DIRTY);
    }

    @Test
    void reconciliar_enviaSnapshotConClaveDeterministica() {
        UUID fileId = UUID.randomUUID();
        Archivo file = Archivo.builder().id(fileId).userId(USER_ID).documentoId("doc").nombre("doc.md")
                .dominio("LEYES").objectName("prod/users/" + USER_ID + "/input/LEYES/doc.md")
                .tamano(10L).tipo("text/markdown").subidoEn(LocalDateTime.now()).build();
        IndiceUsuario index = IndiceUsuario.builder().userId(USER_ID).estado(IndiceEstado.DIRTY).requestedGeneration(4).build();
        when(indiceRepository.findByUserIdForUpdate(USER_ID)).thenReturn(Optional.of(index));
        when(archivoRepository.findIndexableByUserId(USER_ID)).thenReturn(List.of(file));
        when(archivoRepository.findByUserIdAndPendienteEliminacionTrue(USER_ID)).thenReturn(List.of());
        when(mlClient.createIndexJob(any(IndexJobRequest.class))).thenReturn(new IndexJobResponse(
                UUID.randomUUID(), "QUEUED", "DOWNLOAD", "en cola", null, 4,
                OffsetDateTime.now().toString(), null, null));
        when(indiceRepository.save(any(IndiceUsuario.class))).thenAnswer(invocation -> invocation.getArgument(0));

        service.reconciliarUsuario(USER_ID);

        assertThat(index.getEstado()).isEqualTo(IndiceEstado.QUEUED);
        assertThat(index.getMlJobId()).isNotNull();
        verify(mlClient).createIndexJob(any(IndexJobRequest.class));
    }
}
