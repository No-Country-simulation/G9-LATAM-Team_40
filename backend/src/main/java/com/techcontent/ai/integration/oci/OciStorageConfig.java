package com.techcontent.ai.integration.oci;

import com.oracle.bmc.auth.AuthenticationDetailsProvider;
import com.oracle.bmc.auth.SimpleAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OciStorageConfig {

    @Value("${oci.tenancy}")
    private String tenancyId;

    @Value("${oci.user}")
    private String userId;

    @Value("${oci.fingerprint}")
    private String fingerprint;

    @Value("${oci.private-key-path}")
    private String privateKeyPath;

    @Value("${oci.region}")
    private String region;

    @Bean
    public ObjectStorageClient objectStorageClient() {
        AuthenticationDetailsProvider provider = SimpleAuthenticationDetailsProvider.builder()
                .tenantId(tenancyId)
                .userId(userId)
                .fingerprint(fingerprint)
                .privateKey(privateKeyPath)
                .build();

        ObjectStorageClient client = ObjectStorageClient.builder().build(provider);
        client.setRegion(region);
        return client;
    }
}
