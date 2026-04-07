# Design-to-Spec Capability

> Convert product concept and design artifacts into technical specifications
> consumable by implementation nodes. Bridges the gap between "what to build"
> and "how to build it".

## Goal

Transform product-concept.json, experience-map, and infrastructure decisions into
concrete technical specifications: API endpoint definitions, database schemas, and
communication protocol specs. These become the single source of truth that all
implementation nodes consume via Context Pull.

## Prerequisites

1. product-concept.json exists (concept crystallization complete)
2. Experience map exists (optional but improves spec quality)
3. infra-design.json exists (optional — determines protocol choices)

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `api-spec.json` | API endpoint definitions: routes, methods, request/response schemas, auth requirements |
| `db-schema.md` | Database table/collection design: fields, types, relations, indexes, constraints |

### Optional Outputs

| Output | When |
|--------|------|
| `protocol-spec.md` | Realtime communication protocol: message types, event formats, connection lifecycle. Only when project uses WebSocket/gRPC streaming/SSE. |

### Required Quality

- Every entity in product-concept has corresponding DB tables/collections
- Every user-facing operation in experience-map has a corresponding API endpoint
- Request/response schemas have concrete field names and types (not "user object")
- API authentication requirements are specified per endpoint (public / auth required / role-restricted)
- DB indexes match the expected query patterns from the API spec

## Methodology Guidance (not steps)

- **Entity-first schema design**: Extract entities from product-concept → define DB tables → derive API endpoints from CRUD + business operations on those entities
- **API contract first**: Define the interface before implementation — consumers (web/mobile) and producers (backend) code against the same spec
- **Protocol from interactions**: For each realtime interaction in experience-map (chat, notifications, presence), define the message type, direction (client→server / server→client / bidirectional), and payload schema
- **Version strategy**: API routes use version prefix (e.g., `/v1/`). DB migrations use sequential numbering.
- **Consistency check**: Every API endpoint that writes data must correspond to a DB table. Every DB table should be reachable from at least one API endpoint.

## Downstream Consumers

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `api-spec.json` | `endpoints[]` | translate (implement nodes) | required | Implement nodes need to know which endpoints to build |
| `api-spec.json` | `endpoints[].request_schema`, `response_schema` | demo-forge | required | Demo-forge constructs API requests from schema definitions |
| `db-schema.md` | table definitions | translate (implement nodes) | required | Implement nodes need the data model to write ORM/migration code |
| `protocol-spec.md` | message types | translate (implement nodes) | optional | Only realtime projects need protocol implementation |

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Upstream-Baseline-Validation: spec must be consistent with product-concept
- defensive-patterns.md: error response schemas, pagination patterns

## Composition Hints

### Single Node (default)
One design-to-spec node outputs all technical specifications for the project.

### Split by Service
For monorepo with multiple services: spec-user-service, spec-messaging-service, spec-payment-service.

### Skip Entirely
When goals do not include create or rebuild (existing code already has implicit specs).
When translating between stacks (source code IS the spec).
