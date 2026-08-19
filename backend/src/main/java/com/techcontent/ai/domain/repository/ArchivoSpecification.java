package com.techcontent.ai.domain.repository;

import com.techcontent.ai.api.dto.request.ArchivoFiltroDTO;
import com.techcontent.ai.domain.model.Archivo;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.jpa.domain.Specification;
import java.util.ArrayList;
import java.util.List;

public class ArchivoSpecification {

    public static Specification<Archivo> conFiltros(ArchivoFiltroDTO filtros) {
        return (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (filtros.getNombre() != null && !filtros.getNombre().isEmpty()) {
                predicates.add(cb.like(cb.lower(root.get("nombre")), "%" + filtros.getNombre().toLowerCase() + "%"));
            }
            if (filtros.getTipo() != null && !filtros.getTipo().isEmpty()) {
                predicates.add(cb.equal(root.get("tipo"), filtros.getTipo()));
            }
            if (filtros.getUserId() != null) {
                predicates.add(cb.equal(root.get("userId"), filtros.getUserId()));
            }
            if (filtros.getFechaInicio() != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("subidoEn"), filtros.getFechaInicio()));
            }
            if (filtros.getFechaFin() != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("subidoEn"), filtros.getFechaFin()));
            }

            return cb.and(predicates.toArray(new Predicate[0]));
        };
    }
}
