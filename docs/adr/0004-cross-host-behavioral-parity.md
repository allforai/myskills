---
status: accepted
---

# Preserve host execution mechanisms; align business decisions

Claude uses Workflow while Codex uses its own executor. During the grill-with-docs session, the user confirmed retaining these distinct mechanisms while requiring the same business decisions for equivalent logical task graphs, evidence, and events: admission, repair-budget authorization, acceptance, and stopping.

Both hosts must be checked against the same contract scenarios; scheduling order, invocation mechanisms, and log formats need not match. This avoids forcing either host into an unsuitable common engine while making semantic divergence testable. Which deterministic implementations can safely be shared remains an implementation-design decision, not an authorization to merge the engines or replace real-host acceptance with unit tests.
