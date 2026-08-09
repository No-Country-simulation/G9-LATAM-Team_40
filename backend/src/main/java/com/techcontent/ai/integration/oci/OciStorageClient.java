package com.techcontent.ai.integration.oci;

import com.oracle.bmc.objectstorage.ObjectStorage;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import com.oracle.bmc.objectstorage.responses.PutObjectResponse;
import com.oracle.bmc.model.BmcException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.util.UUID;

@Slf4j
@Service
public class OciStorageClient {

    private final ObjectStorage objectStorageClient;

    @Value("${oci.bucket.name}")
    private String bucketName;

    @Value("${oci.namespace}")
    private String namespace;

    @Value("${oci.region}")
    private String region;

    public OciStorageClient(ObjectStorage objectStorageClient) {
        this.objectStorageClient = objectStorageClient;
    }

    public String subirArchivo(MultipartFile file) {
        String objectName = UUID.randomUUID() + "-" + file.getOriginalFilename();

        try (InputStream inputStream = file.getInputStream()) {
            PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                    .namespaceName(namespace)
                    .bucketName(bucketName)
                    .objectName(objectName)
                    .contentType(file.getContentType())
                    .contentLength(file.getSize())
                    .putObjectBody(inputStream)
                    .build();

            PutObjectResponse response = objectStorageClient.putObject(putObjectRequest);
            log.info("Archivo subido exitosamente a OCI. ETag: {}", response.getETag());
            
            return objectName;
        } catch (BmcException e) {
            log.error("Error de OCI SDK o Timeout al subir archivo: {}", e.getMessage(), e);
            throw new RuntimeException("Fallo en la comunicación con OCI Object Storage por timeout o credenciales.", e);
        } catch (IOException e) {
            log.error("Error al leer el stream del archivo multipart: {}", e.getMessage(), e);
            throw new RuntimeException("No se pudo procesar el archivo para subirlo a OCI.", e);
        }
    }

    public String obtenerUrlPublica(String objectName) {
        return String.format("https://objectstorage.%s.oraclecloud.com/n/%s/b/%s/o/%s",
                region, namespace, bucketName, objectName);
    }
}
