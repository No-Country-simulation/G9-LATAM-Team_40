package com.techcontent.ai;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import org.springframework.boot.test.mock.mockito.MockBean;

@SpringBootTest
@ActiveProfiles("test")
class TechContentAiApplicationTests {

    @MockBean
    private ObjectStorageClient objectStorageSdkClient;

    @Test
    void contextLoads() {
    }
}