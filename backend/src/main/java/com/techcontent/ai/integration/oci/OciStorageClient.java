package com.techcontent.ai.integration.oci;

import com.oracle.bmc.model.BmcException;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.DeleteObjectRequest;
import com.oracle.bmc.objectstorage.requests.GetObjectRequest;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

import java.io.InputStream;

@Component
@Slf4j
public class OciStorageClient {

    private final ObjectStorageClient objectStorageClient;

    @Value("${oci.namespace}")
    private String namespace;

    public OciStorageClient(@Lazy ObjectStorageClient objectStorageClient) {
        this.objectStorageClient = objectStorageClient;
    }

    public String upload(String bucketName, String objectName, InputStream inputStream,
                         long contentLength, String contentType) {
        try {
            PutObjectRequest request = PutObjectRequest.builder()
                    .namespaceName(namespace)
                    .bucketName(bucketName)
                    .objectName(objectName)
                    .putObjectBody(inputStream)
                    .contentLength(contentLength)
                    .contentType(contentType)
                    .build();
            objectStorageClient.putObject(request);
            log.info("Archivo subido exitosamente a OCI: {}", objectName);
            return internalUrl(bucketName, objectName);
        } catch (BmcException e) {
            if (e.isTimeout()) {
                throw new OciStorageTimeoutException("Tiempo de espera agotado al subir el archivo a OCI", e);
            }
            throw new RuntimeException("Fallo en OCI al subir archivo (HTTP " + e.getStatusCode() + ")", e);
        } catch (Exception e) {
            throw new RuntimeException("Error inesperado en carga OCI", e);
        }
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
            log.error("Error al descargar archivo {}", objectName, e);
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
            log.info("Archivo eliminado exitosamente de OCI: {}", objectName);
        } catch (Exception e) {
            log.error("Error al eliminar archivo {}", objectName, e);
            throw new RuntimeException("Error en eliminación desde OCI", e);
        }
    }

    private String internalUrl(String bucketName, String objectName) {
        return "oci://" + bucketName + "/" + objectName;
    }
}
