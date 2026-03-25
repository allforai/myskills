---
name: cr-fullstack
description: >
  Use when user wants to "replicate full project", "fullstack replication",
  "replicate both frontend and backend", "fullstack rewrite", "clone entire project",
  or mentions analyzing both frontend and backend code together for cross-layer consistency.
version: "1.0.0"
---

# Fullstack Replication Analysis Perspective

## Overview

Fullstack replication delegates cr-backend + cr-frontend to scan their respective layers, then additionally performs cross-validation and infrastructure scanning. The goal is not "run it twice" but coordinated single-pass analysis + cross-layer consistency assurance.

---

## Analysis Perspectives

Fullstack inherits backend four perspectives (entry/service/data/cross-cutting) and frontend four perspectives (page-route/component/state/interaction), plus:

### Cross-Validation Perspective

Contracts and consistency between frontend and backend:

- **API Contract Alignment**: frontend-called endpoints vs backend-exposed endpoints (path/method/params/response)
- **Data Type Alignment**: frontend type definitions vs backend entity fields (name/type/optionality)
- **Auth Propagation**: backend auth requirements vs frontend token management and route guards
- **Error Mapping**: backend error codes/formats vs frontend error handling logic
- **Real-Time Communication**: WebSocket/SSE event names and data format alignment across frontend/backend

### Infrastructure Perspective

Infrastructure supporting frontend and backend:

- **Container Orchestration**: Docker config, inter-service networking, build pipelines
- **Reverse Proxy**: API gateway, path forwarding, CORS config
- **Environment Variables**: frontend and backend respective configs + shared configs
- **Scheduled Tasks**: Cron config, scheduling system
- **Deployment Manifest**: K8s/Compose config, service dependencies

---

## Phase 2 Enhancements

On top of core Phase 2, add these fullstack-specific steps:

### 2a. Project Structure Detection

Auto-detect project type:
- **Monorepo pattern**: detect backend/ + frontend/ (or server/ + client/ variants) separate dirs
- **Single-dir fullstack pattern**: frontend and backend in same dir (e.g., pages/ + api/ coexisting in fullstack framework)
- Record detection result to source-summary.json `project_structure` field

### 2b. Delegated Layer Scanning

- Delegate cr-backend Phase 2b instructions to scan backend portion
- Delegate cr-frontend Phase 2b instructions to scan frontend portion
- Both scans' module summaries written separately to source-summary.json

### 2c. Infrastructure Scanning

Additionally scan and record:
- Docker/container orchestration config
- Reverse proxy/API gateway config
- Environment variable inventory (frontend, backend, shared)
- Scheduled task config
- CI/CD pipeline config

### 2d. source-summary.json Enhanced Fields

```
Add these top-level fields:
- infrastructure: infrastructure config summary
- api_call_map: frontend -> backend API call mapping
  - frontend_component: caller component
  - backend_endpoint: callee endpoint
  - data_shape: request/response data structure
  - auth_required: whether authentication needed
```

---

## Phase 3-pre: Generate extraction-plan (Fullstack Enhanced)

Beyond cr-backend and cr-frontend's respective extraction-plan fields, fullstack mode additionally generates:

- `api_contract_files`: frontend-backend API contract files (OpenAPI spec, GraphQL schema, tRPC router, or handwritten type definitions)
- `cross_layer_mapping`: frontend call files <-> backend handler files correspondence (LLM infers from source-summary.api_call_map)

## Phase 3: Fullstack Enhancements

### task-inventory Enhancement

- Merge frontend and backend tasks, eliminate duplicates (same business operation's frontend/backend tasks merge into one)
- Each task adds `layer` field:
  - `backend` — pure backend task (scheduled tasks, queue consumers, etc.)
  - `frontend` — pure frontend task (UI-only interaction, local computation, etc.)
  - `fullstack` — cross frontend-backend task (user action -> API -> processing -> response -> UI update)

### business-flows Enhancement

- Build complete cross-frontend-backend user flows
- Each flow step annotated with layer (frontend/backend)

### Cross-Layer Consistency Check

LLM checks for actual inconsistencies based on extraction-plan.cross_layer_mapping, writes to task/flow `flags` field. Common but **not necessarily present** inconsistency types:

- API parameter/response mismatch
- Auth propagation breakage
- Field type inconsistency
- Orphan endpoints (one side has it, other side doesn't call it)
- Unhandled error codes

> **Note**: Don't assume all projects have the above problems. LLM judges from actual code.

---

## Phase 4 Enhancements

- Validation scripts run with `--fullstack` flag
- Additional check metrics:
  - **API call match rate**: do all frontend-called endpoints exist in backend (and vice versa)?
  - **Field alignment rate**: are same-named data structures' fields consistent across frontend/backend?
  - Match/alignment results written to verification report's `cross_layer_validation` section

---

## Load Core Protocol

> Core protocol details: `./skills/code-replicate-core.md`
