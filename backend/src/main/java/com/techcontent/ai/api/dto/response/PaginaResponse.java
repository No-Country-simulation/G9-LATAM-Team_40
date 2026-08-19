package com.techcontent.ai.api.dto.response;

import java.util.List;

public record PaginaResponse<T>(
        List<T> items,
        int page,
        int size,
        long totalElements,
        int totalPages
) {
    public PaginaResponse {
        items = List.copyOf(items);
    }
}
