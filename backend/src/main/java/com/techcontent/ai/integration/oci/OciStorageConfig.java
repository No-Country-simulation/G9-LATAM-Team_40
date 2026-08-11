package com.techcontent.ai.integration.oci;
import com.oracle.bmc.auth.*;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.*;
import org.springframework.web.client.RestClient;
import java.io.FileInputStream;

@Configuration
public class OciStorageConfig {
    @Value("${oci.tenancy}") private String tId;
    @Value("${oci.user}") private String uId;
    @Value("${oci.fingerprint}") private String fp;
    @Value("${oci.private-key-path}") private String pkp;
    @Value("${oci.region}") private String reg;

    @Bean
    public ObjectStorageClient objectStorageClient() {
        var provider = SimpleAuthenticationDetailsProvider.builder()
                .tenantId(tId).userId(uId).fingerprint(fp)
                .privateKeySupplier(() -> { try { return new FileInputStream(pkp); } catch (Exception e) { throw new RuntimeException(e); }})
                .build();
                
        ObjectStorageClient client = ObjectStorageClient.builder().build(provider);
        client.setRegion(reg);
        return client;
    }
    @Bean public RestClient restClient() { return RestClient.create(); }
}
