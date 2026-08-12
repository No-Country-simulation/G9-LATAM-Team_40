package com.techcontent.ai.integration.oci;

import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.model.CreatePreauthenticatedRequestDetails;
import com.oracle.bmc.objectstorage.model.PreauthenticatedRequest;
import com.oracle.bmc.objectstorage.requests.CreatePreauthenticatedRequestRequest;
import com.oracle.bmc.objectstorage.responses.CreatePreauthenticatedRequestResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.oracle.bmc.model.BmcException;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;

import java.io.ByteArrayInputStream;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;

@ExtendWith(MockitoExtension.class)
class OciStorageClientTest {

    @Mock
    private ObjectStorageClient objectStorageClient;

    private OciStorageClient ociStorageClient;

    @BeforeEach
    void setUp() {
        ociStorageClient = new OciStorageClient(objectStorageClient);

        ReflectionTestUtils.setField(
                ociStorageClient,
                "region",
                "sa-saopaulo-1"
        );

        ReflectionTestUtils.setField(
                ociStorageClient,
                "namespace",
                "namespace-prueba"
        );
    }

    @Test
    void getPresignedUrl_conObjetoValido_generaUrlTemporalDeLectura() {
        PreauthenticatedRequest preauthenticatedRequest =
                PreauthenticatedRequest.builder()
                        .accessUri("/p/token-temporal/n/namespace-prueba/b/archivos/o/documento.pdf")
                        .build();

        CreatePreauthenticatedRequestResponse response =
                CreatePreauthenticatedRequestResponse.builder()
                        .__httpStatusCode__(200)
                        .preauthenticatedRequest(preauthenticatedRequest)
                        .build();

        when(objectStorageClient.createPreauthenticatedRequest(any()))
                .thenReturn(response);

        long tiempoAntes = System.currentTimeMillis();

        String url = ociStorageClient.getPresignedUrl(
                "archivos",
                "documento.pdf",
                30
        );

        long tiempoDespues = System.currentTimeMillis();

        assertEquals(
                "https://objectstorage.sa-saopaulo-1.oraclecloud.com"
                        + "/p/token-temporal/n/namespace-prueba/b/archivos/o/documento.pdf",
                url
        );

        ArgumentCaptor<CreatePreauthenticatedRequestRequest> captor =
                ArgumentCaptor.forClass(CreatePreauthenticatedRequestRequest.class);

        verify(objectStorageClient)
                .createPreauthenticatedRequest(captor.capture());

        CreatePreauthenticatedRequestRequest request = captor.getValue();

        assertEquals("namespace-prueba", request.getNamespaceName());
        assertEquals("archivos", request.getBucketName());

        CreatePreauthenticatedRequestDetails details =
                request.getCreatePreauthenticatedRequestDetails();

        assertEquals("documento.pdf", details.getObjectName());

        assertEquals(
                CreatePreauthenticatedRequestDetails.AccessType.ObjectRead,
                details.getAccessType()
        );

        long expiracion = details.getTimeExpires().getTime();
        long treintaMinutos = 30L * 60L * 1000L;

        assertTrue(expiracion >= tiempoAntes + treintaMinutos);
        assertTrue(expiracion <= tiempoDespues + treintaMinutos);
    }

    @Test
    void upload_cuandoOciProduceTimeout_lanzaExcepcionEspecifica() {
        BmcException timeout = mock(BmcException.class);

        when(timeout.isTimeout()).thenReturn(true);

        doThrow(timeout)
                .when(objectStorageClient)
                .putObject(any(PutObjectRequest.class));

        assertThrows(
                OciStorageTimeoutException.class,
                () -> ociStorageClient.upload(
                        "archivos",
                        "documento.pdf",
                        new ByteArrayInputStream("contenido".getBytes()),
                        9L,
                        "application/pdf"
                )
        );
    }

    @Test
    void getPresignedUrl_cuandoOciProduceTimeout_lanzaExcepcionEspecifica() {
        BmcException timeout = mock(BmcException.class);

        when(timeout.isTimeout()).thenReturn(true);

        when(objectStorageClient.createPreauthenticatedRequest(any()))
                .thenThrow(timeout);

        assertThrows(
                OciStorageTimeoutException.class,
                () -> ociStorageClient.getPresignedUrl(
                        "archivos",
                        "documento.pdf",
                        30
                )
        );
    }
}