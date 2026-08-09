package com.techcontent.ai.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MlResponse {
    private String categoria;
    private Double probabilidad;
    
    @JsonProperty("palabras_clave")
    private String palabrasClave;
}
