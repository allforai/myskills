---
name: cr-backend
description: >
  Use when user wants to "replicate backend", "API rewrite", "backend replication",
  "microservice migration", "reverse engineer API", "clone backend", "port backend to",
  "migrate backend", "rewrite server", or mentions converting existing
  backend/API/microservice code to a different tech stack while preserving behavior.
version: "1.0.0"
---

# Backend Replication Analysis Perspective

## Overview

Backend replication focuses on extracting complete business behavior descriptions from server-side code. The analysis goal is understanding "what the system does" not "what framework it uses", ensuring zero business logic loss when migrating to any target tech stack.

---

## Analysis Perspectives

### Entry Layer

The boundary receiving external requests — all system touchpoints with the outside world:

- **HTTP Routes**: paths, methods, parameter bindings, request/response formats
- **RPC Definitions**: service interface declarations, method signatures, serialization protocols
- **Message Consumers**: queue/topic subscriptions, message formats, consumption acknowledgment
- **CLI Commands**: command names, parameter definitions, output formats
- **Scheduled Task Entries**: scheduling rules, trigger conditions, task parameters

> Entry layer answers: What capabilities does the system expose externally? What is each capability's input/output contract?

### Service Layer

Business logic orchestration — the system's core decisions and coordination:

- **Transaction Boundaries**: which operations must execute atomically, rollback strategies
- **External Service Calls**: which third-party/internal services are called, parameters, response handling
- **Async Task Initiation**: which operations are asynchronized, task parameters, completion callbacks
- **Retry Strategies**: failure retry logic, backoff strategies, max retry counts
- **Business Rules**: conditional judgments, state transitions, computation logic

> Service layer answers: What is the business logic behind each entry point? How does the decision chain flow?

### Data Layer

Persistence operations — how the system stores and retrieves data:

- **Entity Definitions**: data models, field types, relationship mappings, constraints
- **Query Patterns**: common query shapes (filtering, sorting, pagination, aggregation)
- **Migration Scripts**: schema evolution history, data migration logic
- **Cache Strategies**: cached objects, invalidation rules, cache penetration handling

> Data layer answers: What data does the system persist? What are the relationships between data?

### Cross-Cutting Layer

Concerns spanning all layers:

- **Auth/Authorization Chain**: authentication methods, permission check logic, role definitions
- **Middleware Pipeline**: request processing pipeline order and responsibilities
- **Error Handling Strategy**: error classification, error code definitions, error response format
- **Logging Strategy**: log levels, structured log fields, audit logs
- **Configuration Management**: environment variables, config files, feature flags

> Cross-cutting layer answers: Where are the system's security boundaries? How do errors propagate? How is runtime behavior controlled?

---

## Phase 2b Supplementary Instructions

When generating module summaries (source-summary.json modules[]), additionally extract the following backend-specific information:

### API Endpoint Inventory
```
Per endpoint:
- method: HTTP method (GET/POST/PUT/DELETE etc.)
- path: route path (including path parameters)
- auth: requires authentication (yes/no/optional)
- summary: one-sentence description of endpoint purpose
```

### Data Entity Inventory
```
Per entity:
- name: entity name
- key_fields: key field list (name + type)
- relations: relationships with other entities (1:N, N:M etc.)
```

### Authentication Mechanism Summary
```
Record:
- auth_type: authentication method (JWT/Session/OAuth/API Key etc.)
- role_model: role model description
- permission_granularity: permission granularity (API-level/resource-level/field-level)
```

---

## Phase 3-pre: Generate extraction-plan

LLM reads source-summary.json, based on understanding of **this specific backend project**, generates extraction-plan.json:

- `role_sources`: which files define roles/permissions? (could be RBAC config, middleware, decorators, annotations... depends on the project)
- `task_sources`: which files define business entry points? (could be Controllers, Handlers, gRPC Services, CLI Commands, Cron Jobs... depends on the project)
- `flow_sources`: which files contain business orchestration logic? (could be Service methods, Sagas, Pipelines... depends on the project)
- `usecase_sources`: which files contain conditional branches and error handling? (deeper analysis of task_sources)
- `constraint_sources`: which files contain validation rules and hard constraints? (could be Validators, Schemas, Middleware... depends on the project)
- `cross_cutting`: cross-module concerns (auth, logging, error handling) in which files?

**Do not apply framework templates** — must infer from source-summary's actual module structure and key_files.

## Phase 3: Generate fragments per extraction-plan

Per extraction-plan specified files and extraction methods, generate JSON fragments per module.

### Backend Analysis Points

The following are common but **not necessarily present** backend patterns. LLM should note which patterns this project actually uses in the extraction-plan, not assume all projects have them:

- **Async operations**: queue consumers and scheduled tasks may be independent tasks — if the project has async mechanisms, extraction-plan should note them
- **Implicit flows**: middleware chains may constitute implicit business flows — if the project uses middleware pipelines, extraction-plan.cross_cutting should record them
- **Data constraints**: database schema constraints may be constraint sources — if the project has ORM/migration scripts, extraction-plan.constraint_sources should point to them
- **Error code systems**: error code definitions may imply exception scenarios — if the project has unified error codes, extraction-plan.usecase_sources should include them

---

## Load Core Protocol

> Core protocol details: `./skills/code-replicate-core.md`
