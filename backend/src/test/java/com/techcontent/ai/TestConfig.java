package com.techcontent.ai;

import com.oracle.bmc.objectstorage.ObjectStorageClient;
import org.mockito.Mockito;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;

@TestConfiguration
public class TestConfig {

    @Bean
    @Primary
    public ObjectStorageClient objectStorageClient() {
        return Mockito.mock(ObjectStorageClient.class);
    }
}
