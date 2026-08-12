package com.techcontent.ai.integration.oci;

import com.oracle.bmc.model.BmcException;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.DeleteObjectRequest;
import com.oracle.bmc.objectstorage.requests.GetObjectRequest;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import java.io.InputStream;

@Component
@RequiredArgsConstructor
@Slf4j
public class OciStorageClient {

    private final ObjectStorageClient objectStorageClient;

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
            log.error("Error de OCI al subir archivo - HTTP {}: {}", e.getStatusCode(), e.getMessage(), e);
            throw new RuntimeException("Fallo en OCI al subir archivo (HTTP " + e.getStatusCode() + ")", e);
        } catch (Exception e) {
            log.error("Error inesperado al subir archivo a OCI", e);
            throw new RuntimeException("Error inesperado en carga OCI", e);
        }
    }

    public String getPresignedUrl(String bucketName, String objectName, int expirationMinutes) {
        log.info("Generando URL para el objeto: {}", objectName);
        // Retorna la URL pública/base como alternativa estable para la capa de servicios
        return buildPublicUrl(bucketName, objectName);
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