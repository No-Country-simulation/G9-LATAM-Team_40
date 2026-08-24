package com.techcontent.ai.integration.ml;

import com.techcontent.ai.domain.service.IndiceUsuarioService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;

@Configuration
@EnableScheduling
@RequiredArgsConstructor
public class IndexacionConfig {

    private final IndiceUsuarioService indiceUsuarioService;

    @Scheduled(fixedDelayString = "${index.reconcile.delay.ms:5000}")
    public void reconciliarIndicesPrivados() {
        indiceUsuarioService.reconciliarTodos();
    }
}
