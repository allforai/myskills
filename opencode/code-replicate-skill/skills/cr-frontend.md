---
name: cr-frontend
description: >
  Use when user wants to "replicate frontend", "component rewrite", "frontend replication",
  "React migration", "Vue migration", "Flutter migration", "React Native migration",
  "clone UI", "port frontend to", "migrate frontend", "rewrite client app",
  "component replication", "UI replication", "mobile replication", or mentions converting
  existing frontend/mobile code to a different framework while preserving behavior.
version: "1.0.0"
---

# Frontend Replication Analysis Perspective

## Overview

Frontend replication focuses on extracting complete user experience descriptions from client-side code. The analysis goal is understanding "what users can do and see" not "what component library it uses", ensuring zero user experience loss when migrating to any target framework.

---

## Analysis Perspectives

### Page/Route Layer

Views users can reach — the application's navigation skeleton:

- **Route Definitions**: path structure, parameterized routes, nested route hierarchy
- **Navigation Structure**: main nav, sidebar, breadcrumbs, tab switching
- **Deep Links**: externally accessible page paths, share link support
- **Route Guards**: access control (login required, role restrictions, conditional redirects)
- **Page Layouts**: layout templates, shared regions (Header/Footer/Sidebar)

> Route layer answers: What pages can users reach? How do pages connect? Which pages have access restrictions?

### Component Layer

Reusable UI units — the interface building blocks:

- **Props Interface**: accepted input parameters, types, defaults, required fields
- **Events/Callbacks**: events emitted outward, callback function signatures
- **Slots/Children**: content distribution mechanism, named slots
- **Component Lifecycle**: initialization logic, cleanup on destroy, dependent data loading
- **Component Hierarchy**: parent-child relationships, composition patterns, HOCs/decorators

> Component layer answers: What reusable units compose the interface? What are their input/output contracts?

### State Layer

Data flow — how data is stored and transmitted:

- **Global State Management**: app-level shared state, state partitions/modules
- **Local State**: component internal state, form state
- **Server State Cache**: API response caching, optimistic updates, background refresh
- **Derived State**: computed properties, selectors, data transformation pipelines
- **State Persistence**: local storage, session storage, URL state

> State layer answers: Where does data come from? How does it flow? Where is it consumed?

### Interaction Layer

User action chains — user-interface interaction patterns:

- **Form Submission Flow**: validate -> submit -> feedback (success/failure) -> navigation
- **Search/Filter Flow**: input -> debounce -> request -> result update -> pagination
- **Real-Time Updates**: WebSocket/SSE push -> state update -> UI refresh
- **Animations/Transitions**: page switch animations, list add/remove animations, loading states
- **Gestures/Shortcuts**: drag, swipe, keyboard shortcuts, multi-touch

> Interaction layer answers: How does the system respond to each user action? What is the complete action sequence?

---

## Phase 2b Supplementary Instructions

When generating module summaries (source-summary.json modules[]), additionally extract the following frontend-specific information:

### Page Inventory
```
Per page:
- route: route path
- title: page title/name
- guard: access control condition (none/login/role)
- layout: layout template used
```

### Component Tree
```
Record component hierarchy:
- name: component name
- children: child component list
- props_count: Props count
- events_count: Events count
- complexity: low/medium/high (based on child count and logic amount)
```

### API Call Inventory
```
Record frontend-to-backend call mapping:
- component: component/page making the call
- endpoint: API endpoint called (method + path)
- trigger: trigger timing (mount/click/submit/interval)
- error_handling: error handling method (toast/redirect/retry/inline)
```

---

## Phase 3-pre: Generate extraction-plan

LLM reads source-summary.json, based on understanding of **this specific frontend project**, generates extraction-plan.json:

- `role_sources`: which files define permission control? (could be route guards, permission components, menu config... depends on project)
- `screen_sources`: which files define pages/views? (could be pages/, app/, screens/, route configs... depends on project and framework)
- `task_sources`: which files contain user action entries? (could be form components, action handlers, event handlers... depends on project)
- `flow_sources`: which files contain user interaction chains? (could be page navigation logic, state machines, store actions... depends on project)
- `usecase_sources`: which files contain conditional branches? (screen_sources + error handling components)
- `cross_cutting`: cross-page shared mechanisms (auth, i18n, theming, toast...) in which files?

**Do not apply framework templates** — must infer from source-summary's actual module structure and key_files.

## Phase 3: Generate fragments per extraction-plan

Per extraction-plan specified files and extraction methods, generate JSON fragments per module.

### Frontend Analysis Points

The following are common but **not necessarily present** frontend patterns. LLM should note which patterns this project actually uses in the extraction-plan:

- **Empty/loading states**: if the project has data display pages, their empty/loading/error states may be use-case scenarios
- **Responsive layouts**: if the project has multi-device adaptation logic, extraction-plan.screen_sources should note related configs
- **Offline behavior**: if the project has Service Worker or local caching, extraction-plan.constraint_sources should record them
- **Accessibility**: if the project has ARIA/a11y implementation, extraction-plan.cross_cutting should note them

---

## Load Core Protocol

> Core protocol details: `./skills/code-replicate-core.md`
