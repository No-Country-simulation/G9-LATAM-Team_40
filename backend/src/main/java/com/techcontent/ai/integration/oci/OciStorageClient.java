package com.techcontent.ai.integration.oci;

import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.InputStream;

@Component
@RequiredArgsConstructor
public class OciStorageClient {

    private final ObjectStorageClient objectStorageClient;

    @Value("${oci.region}")
    private String region;

    public String upload(String bucketName, String objectName, InputStream inputStream, long contentLength, String contentType) {
        String namespaceName = objectStorageClient.getNamespace(
                com.oracle.bmc.objectstorage.requests.GetNamespaceRequest.builder().build()
        ).getValue();

        PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                .namespaceName(namespaceName)
                .bucketName(bucketName)
                .objectName(objectName)
                .putObjectBody(inputStream)
                .contentLength(contentLength)
                .contentType(contentType)
                .build();

        objectStorageClient.putObject(putObjectRequest);
        
        return "https://objectstorage." + region + ".oraclecloud.com/n/" + namespaceName + "/b/" + bucketName + "/o/" + objectName;
    }
}