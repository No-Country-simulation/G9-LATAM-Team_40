package com.techcontent.ai.integration.ml;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.UUID;

public record IndexGraphResponse(
        @JsonProperty("user_id") UUID userId,
        @JsonProperty("release_id") String releaseId,
        Long generation,
        @JsonProperty("created_at") String createdAt,
        @JsonProperty("json_data") Object jsonData
) {}
