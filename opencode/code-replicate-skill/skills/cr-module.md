---
name: cr-module
description: >
  Use when user wants to "replicate module", "module replication", "replicate specific module",
  "migrate specific module", "extract module", "module migration",
  "replicate specific feature", or mentions replicating a subset of code
  with attention to dependency boundaries.
version: "1.0.0"
---

# Module Replication Analysis Perspective

## Overview

Module replication analyzes a specified module and proactively scans its external dependency boundaries. Difference from scope=modules: cr-module not only analyzes the target module itself but proactively discovers, presents, and helps users decide on all dependency relationships, solving the "module boundary isn't clean" problem.

---

## Analysis Perspectives

Module replication reuses cr-backend or cr-frontend analysis perspectives based on target module type. Additionally focuses on:

### Dependency Boundary Perspective

Connection points between the module and the outside world:

- **Code Dependencies**: import/require of other modules' code (functions, classes, constants, types)
- **Event Dependencies**: emit/publish/dispatch events consumed by which modules, subscribe/listen to which external events
- **Shared Layer Dependencies**: shared infrastructure used (auth, logging, config, database tables, type definitions)
- **Data Dependencies**: reading/writing data tables or cache keys "owned" by other modules
- **Interface Dependencies**: implementing or calling interfaces/protocols defined by other modules

> Boundary perspective answers: If this module were "pulled out", which connections would break?

---

## Phase 2 Enhancements

On top of core Phase 2, add these module-specific steps:

### 2a. Full Project Scan

- Need global perspective to discover dependencies, so scan entire project structure first
- But `key_files` only deeply reads files within the target module (control analysis cost)
- Other modules only read entry files and export definitions (sufficient to identify dependency interfaces)

### 2b. Dependency Boundary Scan

Systematically scan three dependency types:

**Code Dependencies**
- What external modules does the target module import/require
- What exports from the target module do external modules import/require

**Event Dependencies**
- Target module's emit/publish/dispatch events -> which external modules consume them
- Target module's subscribe/listen events -> from which external modules

**Shared Layer Dependencies**
- Shared auth/authorization mechanisms
- Shared logging/config infrastructure
- Shared type definitions/interfaces
- Shared database tables (multiple modules read/write same table)

---

## Phase 2d Enhancements

### Dependency Matrix Display

Show the dependency matrix to the user:

```
Target module: [module-name]

Code dependencies:
  -> module-A: calls 3 functions, uses 2 types
  -> module-B: calls 1 function
  <- module-C: 2 exported functions called

Event dependencies:
  -> event:order.created -> module-D consumes
  <- event:payment.completed <- module-E publishes

Shared layer dependencies:
  <-> shared/auth: uses auth middleware
  <-> shared/db: shares users table
```

### Dependency Decision Collection

For each external dependency, collect user decisions (or auto-recommend based on rules):

| Decision | Meaning | Handling |
|----------|---------|----------|
| `include` | Analyze and replicate together | Include in target module scope, full analysis |
| `external_interface` | Record signatures only | Record function signatures/type definitions, don't analyze implementation |
| `event_contract` | Record event schema only | Record event names and data formats |
| `prerequisite` | Mark as precondition | Record as task.prerequisites, don't analyze |

### source-summary.json Enhancements

Module-level enhanced fields written to modules[]:

```
modules[target].dependencies: [
  {
    "target": "module-A",
    "type": "code|event|shared",
    "direction": "outbound|inbound|bidirectional",
    "details": "calls getUserById, formatDate",
    "boundary_decision": "include|external_interface|event_contract|prerequisite"
  }
]
```

---

## Phase 3-pre: Generate extraction-plan (Module Enhanced)

Beyond cr-backend/cr-frontend's standard extraction-plan fields, module mode additionally generates:

- `boundary_interfaces`: target module's externally exposed interface inventory (from Phase 2d dependency matrix)
- `external_deps_mapping`: each external dependency's handling decision (include / external_interface / event_contract / prerequisite)

## Phase 3: Generate fragments per extraction-plan

- Only generate complete artifacts for target module + `include`-decided modules
- `external_interface` dependencies: recorded in related task's `prerequisites` field
- `event_contract` dependencies: record event names and data formats
- `prerequisite` dependencies: recorded as preconditions
- task-inventory tasks related to external dependencies add `external_deps` field listing dependency inventory

---

## Load Core Protocol

> Core protocol details: `./skills/code-replicate-core.md`
