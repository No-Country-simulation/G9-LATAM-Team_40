package com.techcontent.ai.integration.ml;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.UUID;

public record IndexJobRequest(
        @JsonProperty("user_id") UUID userId,
        long generation,
        @JsonProperty("idempotency_key") String idempotencyKey,
        @JsonProperty("purge_previous_releases") boolean purgePreviousReleases,
        List<IndexDocumentRequest> documentos
) {}
