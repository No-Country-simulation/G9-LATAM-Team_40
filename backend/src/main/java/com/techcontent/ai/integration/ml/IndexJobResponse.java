package com.techcontent.ai.integration.ml;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.UUID;

public record IndexJobResponse(
        @JsonProperty("job_id") UUID jobId,
        String status,
        String stage,
        String message,
        @JsonProperty("release_id") String releaseId,
        long generation,
        @JsonProperty("created_at") String createdAt,
        @JsonProperty("started_at") String startedAt,
        @JsonProperty("finished_at") String finishedAt
) {}
