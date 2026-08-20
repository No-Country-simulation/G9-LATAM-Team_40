package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.repository.CategoriaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class CategoriaService {

    private final CategoriaRepository categoriaRepository;

    public List<CategoriaResponse> listarConConteo(UUID userId) {
        return categoriaRepository.findCategoriasConConteoByUserId(userId);
    }
}