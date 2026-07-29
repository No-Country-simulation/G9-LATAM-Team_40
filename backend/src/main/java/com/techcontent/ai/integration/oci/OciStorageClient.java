package com.techcontent.ai.integration.oci;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.InputStream;

/**
 * Cliente para OCI Object Storage.
 * TODO: implementar con OCI Java SDK cuando las credenciales esten disponibles.
 * Actualmente retorna URLs placeholder para no bloquear el desarrollo.
 */
@Slf4j
@Component
public class OciStorageClient {

    public String upload(String bucketName, String objectName, InputStream content, String contentType) {
        // TODO: reemplazar con implementacion real del OCI Java SDK
        // ObjectStorageClient client = ...
        // PutObjectRequest putRequest = PutObjectRequest.builder()...build();
        // client.putObject(putRequest);
        log.warn("OCI Storage no configurado. Retornando URL placeholder para objeto: {}", objectName);
        return "https://objectstorage.placeholder.oraclecloud.com/n/placeholder/b/" + bucketName + "/o/" + objectName;
    }
}
