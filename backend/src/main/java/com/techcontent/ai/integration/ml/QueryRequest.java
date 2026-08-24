package com.techcontent.ai.integration.ml;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.UUID;

public record QueryRequest(
        String pregunta,
        @JsonProperty("user_id") UUID userId
) {}
