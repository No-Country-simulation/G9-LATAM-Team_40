package com.techcontent.ai.domain.service;

import com.techcontent.ai.api.dto.response.CategoriaResponse;
import com.techcontent.ai.domain.repository.ContenidoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class CategoriaService {

    private final ContenidoRepository contenidoRepository;

    public List<CategoriaResponse> listarConConteo() {
        return contenidoRepository.findCategoriasConConteo();
    }
}
