package com.techcontent.ai.integration.oci;

import com.oracle.bmc.auth.AuthenticationDetailsProvider;
import com.oracle.bmc.auth.SimpleAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;
import java.io.FileInputStream;
import java.io.FileNotFoundException;

@Configuration
@Slf4j
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
        log.info("Inicializando ObjectStorageClient para región: {}", region);

        try {
            AuthenticationDetailsProvider provider = SimpleAuthenticationDetailsProvider.builder()
                    .tenantId(tenancyId)
                    .userId(userId)
                    .fingerprint(fingerprint)
                    .privateKeySupplier(() -> {
                        try {
                            return new FileInputStream(privateKeyPath);
                        } catch (FileNotFoundException e) {
                            log.error("No se encontró archivo de llave privada: {}", privateKeyPath);
                            throw new RuntimeException("Archivo de llave privada no encontrado en: " + privateKeyPath, e);
                        }
                    })
                    .build();

            ObjectStorageClient client = ObjectStorageClient.builder()
                    .build(provider);

            client.setRegion(region);
            log.info("✅ ObjectStorageClient inicializado exitosamente");
            return client;

        } catch (Exception e) {
            log.error("❌ Error al inicializar ObjectStorageClient", e);
            throw new RuntimeException("Fallo al inicializar cliente OCI: " + e.getMessage(), e);
        }
    }

    @Bean
    public RestClient restClient() {
        log.info("Inicializando RestClient para llamadas HTTP");
        return RestClient.create();
    }
}