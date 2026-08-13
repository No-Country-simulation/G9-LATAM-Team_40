package com.techcontent.ai.integration.oci;

import com.oracle.bmc.model.BmcException;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.DeleteObjectRequest;
import com.oracle.bmc.objectstorage.requests.GetObjectRequest;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import java.io.InputStream;
import org.springframework.context.annotation.Lazy;

import com.oracle.bmc.objectstorage.model.CreatePreauthenticatedRequestDetails;
import com.oracle.bmc.objectstorage.model.PreauthenticatedRequest;
import com.oracle.bmc.objectstorage.requests.CreatePreauthenticatedRequestRequest;
import com.oracle.bmc.objectstorage.responses.CreatePreauthenticatedRequestResponse;
import com.oracle.bmc.objectstorage.ObjectStorage;
import org.springframework.context.annotation.Lazy;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.UUID;

@Component

@Slf4j
public class OciStorageClient {

    private final ObjectStorageClient objectStorageClient;
    
    public OciStorageClient(
        @Lazy ObjectStorageClient objectStorageClient
        ) {
            this.objectStorageClient = objectStorageClient;
            }

    @Value("${oci.region}")
    private String region;

    @Value("${oci.namespace}")
    private String namespace;

    public String upload(String bucketName, String objectName, InputStream inputStream,
                         long contentLength, String contentType) {
        try {
            log.info("📤 Iniciando carga de archivo a OCI");

            PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                    .namespaceName(namespace)
                    .bucketName(bucketName)
                    .objectName(objectName)
                    .putObjectBody(inputStream)
                    .contentLength(contentLength)
                    .contentType(contentType)
                    .build();

            objectStorageClient.putObject(putObjectRequest);

            String publicUrl = buildPublicUrl(bucketName, objectName);
            log.info("Archivo subido exitosamente a OCI");
            return publicUrl;

         } catch (BmcException e) {
                if (e.isTimeout()) {
                    log.error("Timeout de red al subir archivo a OCI", e);

                    throw new OciStorageTimeoutException(
                            "Tiempo de espera agotado al subir el archivo a OCI",
                            e
                    );
                }

                log.error(
                        "Error de OCI al subir archivo - HTTP {}: {}",
                        e.getStatusCode(),
                        e.getMessage(),
                        e
                );

                throw new RuntimeException(
                        "Fallo en OCI al subir archivo (HTTP "
                                + e.getStatusCode() + ")",
                        e
                );
            }catch (Exception e) {
            log.error("Error inesperado al subir archivo a OCI", e);
            throw new RuntimeException("Error inesperado en carga OCI", e);
        }
    }

    public String getPresignedUrl(
        String bucketName,
        String objectName,
        int expirationMinutes
    ) {
    try {
        Date expiration = Date.from(
                Instant.now().plus(expirationMinutes, ChronoUnit.MINUTES)
        );

        CreatePreauthenticatedRequestDetails details =
                CreatePreauthenticatedRequestDetails.builder()
                        .name("download-" + UUID.randomUUID())
                        .objectName(objectName)
                        .accessType(
                                CreatePreauthenticatedRequestDetails.AccessType.ObjectRead
                        )
                        .timeExpires(expiration)
                        .build();

        CreatePreauthenticatedRequestRequest request =
                CreatePreauthenticatedRequestRequest.builder()
                        .namespaceName(namespace)
                        .bucketName(bucketName)
                        .createPreauthenticatedRequestDetails(details)
                        .build();

        CreatePreauthenticatedRequestResponse response =
                objectStorageClient.createPreauthenticatedRequest(request);

        PreauthenticatedRequest preauthenticatedRequest =
                response.getPreauthenticatedRequest();

        String accessUri = preauthenticatedRequest.getAccessUri();

        return String.format(
                "https://objectstorage.%s.oraclecloud.com%s",
                region,
                accessUri
        );

        } catch (BmcException e) {
        if (e.isTimeout()) {
            log.error("Timeout de red al generar URL temporal de OCI", e);

            throw new OciStorageTimeoutException(
                    "Tiempo de espera agotado al generar la URL temporal de OCI",
                    e
            );
        }

        log.error(
                "Error de OCI al generar URL temporal - HTTP {}: {}",
                e.getStatusCode(),
                e.getMessage(),
                e
        );

        throw new RuntimeException(
                "Fallo en OCI al generar URL temporal (HTTP "
                        + e.getStatusCode() + ")",
                e
            );
        }
    }

    public String getPublicUrl(String bucketName, String objectName) {
        return buildPublicUrl(bucketName, objectName);
    }

    public InputStream download(String bucketName, String objectName) {
        try {
            GetObjectRequest request = GetObjectRequest.builder()
                    .namespaceName(namespace)
                    .bucketName(bucketName)
                    .objectName(objectName)
                    .build();

            return objectStorageClient.getObject(request).getInputStream();
        } catch (Exception e) {
            log.error("Error al descargar archivo", e);
            throw new RuntimeException("Error en descarga desde OCI", e);
        }
    }

    public void delete(String bucketName, String objectName) {
        try {
            DeleteObjectRequest request = DeleteObjectRequest.builder()
                    .namespaceName(namespace)
                    .bucketName(bucketName)
                    .objectName(objectName)
                    .build();

            objectStorageClient.deleteObject(request);
            log.info("Archivo eliminado exitosamente de OCI");
        } catch (Exception e) {
            log.error("Error al eliminar archivo", e);
            throw new RuntimeException("Error en eliminación desde OCI", e);
        }
    }

    private String buildPublicUrl(String bucketName, String objectName) {
        return String.format("https://objectstorage.%s.oraclecloud.com/n/%s/b/%s/o/%s",
                region, namespace, bucketName, objectName);
    }
}