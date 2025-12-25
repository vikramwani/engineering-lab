# LLM Service

## Overview

This repository contains a production‑grade LLM API service built with FastAPI.
The service is designed with clear separation of concerns, resilience to upstream
failures, and operational visibility in mind.

It serves as a reference implementation for how to wrap an LLM provider behind
a stable, observable, and secure internal API.

---

## Problem Statement

Directly integrating application code with an LLM provider creates tight coupling,
poor error handling, and limited observability.

This service solves that by:
- Centralizing LLM access behind a stable API
- Enforcing authentication and request validation
- Handling retries, timeouts, and upstream failures
- Providing consistent logging and request tracing

---

## Architecture

High‑level components:

Client
  |
  v
FastAPI API Layer
  - Request validation
  - Auth (API key)
  - Request ID propagation
  - HTTP error mapping
  |
  v
LLM Client Abstraction
  - Provider SDK integration
  - Retries & backoff
  - Timeout handling
  - Error normalization
  |
  v
Upstream LLM Provider

---

## Key Design Decisions

### API / Client Separation
The API layer is intentionally decoupled from the LLM client implementation.
This allows:
- Provider swaps without API changes
- Cleaner error mapping
- Easier testing and mocking

### Retries in the Client Layer
Retries and backoff live in the LLM client, not the API.
This ensures:
- The API remains thin and declarative
- Retry behavior is consistent across all callers

### Explicit Error Taxonomy
Upstream failures are mapped to explicit domain errors:
- Rate limiting
- Timeouts
- Temporary unavailability

This avoids leaking provider‑specific exceptions into the API layer.

### Request IDs
Each request is assigned a request ID and propagated through logs,
making it easy to trace behavior across layers.

---

## Failure Modes

The service explicitly handles:
- Invalid input → 400
- Authentication failures → 401
- Rate limiting → 429
- Upstream timeouts → 504
- Upstream outages → 503
- Unexpected errors → 500

---

## Observability

- Structured JSON logging
- Request ID correlation
- Clear error classification

Metrics and tracing are planned extensions.

---

## What Changes at Scale

At higher traffic or multi‑tenant usage, this service would evolve to include:
- Per‑tenant rate limiting
- Caching of frequent prompts
- Cost controls and quotas
- Async request handling
- Distributed tracing
- Horizontal scaling behind a load balancer

---

## Non‑Goals

This service intentionally does **not**:
- Manage prompt templates
- Store conversation history
- Implement user‑facing UI
- Perform long‑running batch jobs

Those concerns belong in higher‑level systems.

---

## Local Development

```bash
uvicorn src.api:app --reload

curl -X POST http://localhost:8000/generate \
  -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"hello"}'
