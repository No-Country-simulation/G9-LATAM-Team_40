package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.repository.CategoriaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class CategoriaService {

    private final CategoriaRepository categoriaRepository;

    public List<CategoriaResponse> listarConConteo() {
        return categoriaRepository.findCategoriasConConteo();
    }
}
