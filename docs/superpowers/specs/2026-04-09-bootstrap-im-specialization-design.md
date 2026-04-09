# Bootstrap IM Specialization Design

> Goal: make `bootstrap` generate materially stronger project-specific node-specs for Telegram-class IM products, so realtime, sync, delivery-state, media, moderation, and weak-network recovery are planned explicitly instead of being discovered late by closure checks.

## 1. Problem

Current `bootstrap` can identify that a project is "chat / IM / multi-client", but the generated specialized workflow is still too soft.

Typical failure mode:

- bootstrap generates generic nodes such as `implement-api`, `implement-mobile-app`, `implement-admin`
- IM-specific infrastructure and state-propagation nodes are missing or under-specified
- critical requirements are discovered only later by Step 3.5 closure checks or concept-acceptance

This is too late. For Telegram-class products, these concerns are not polish; they are core architecture.

## 2. Target

When `bootstrap` detects an IM / realtime messaging product, the generated workflow must:

1. explicitly include IM-critical infrastructure nodes
2. explicitly include IM-critical validation nodes
3. generate node-specs with hard execution contracts, not just broad goals
4. encode cross-device and weak-network behavior as first-class acceptance requirements

At the same time, the specialization system must remain general-purpose:

- prefer `LLM + research` to discover project-specific requirements
- avoid over-hardcoding exact node shapes where the project context should decide
- reserve mandatory rules for responsibilities that are core and routinely missed

## 2.1 Generalization Principle

This skill must handle many product types, not only IM products.

Therefore the specialization strategy is:

1. **Research first**
   Bootstrap should prefer product-context reading, codebase reading, and external/domain research when available.
2. **LLM synthesis second**
   LLM should infer the project-specific workflow from the gathered evidence.
3. **Mandatory responsibility pack third**
   Only for high-risk domains like realtime IM should bootstrap inject a hard minimum responsibility set.

This keeps the system flexible while still preventing common catastrophic omissions.

## 3. Scope

### In scope

- `meta-skill` bootstrap specialization logic
- generated workflow node selection
- generated node-spec contract strength
- IM / Telegram / chat-app style products

### Out of scope

- implementing the actual IM product
- changing non-IM product specialization behavior
- replacing Step 3.5 or concept-acceptance

## 4. Detection Signals

Bootstrap should classify a project as `im_realtime` when enough of the following are present:

### Product-language signals

- "chat"
- "messaging"
- "telegram"
- "group chat"
- "channel"
- "direct message"
- "read receipt"
- "message sync"
- "online status"
- "notification"

### Feature signals

- one-to-one messaging
- group chat
- message delivery/read states
- media sending
- message search
- mute / notification preferences
- multi-device login
- message deletion / recall
- admin moderation

### Technical signals

- websocket / socket / realtime transport
- push notifications
- object storage / CDN for media
- offline sync
- search indexing

If product-language signals plus feature signals strongly match, bootstrap should force the `im_realtime` specialization even before technical signals are confirmed.

## 5. Specialization Rule

Once `im_realtime` is detected, bootstrap must not settle for generic implementation nodes alone.

It must append a mandatory IM specialization pack.

Important:

- this pack defines **responsibilities**, not rigid node names
- bootstrap should still let LLM combine, split, or rename nodes based on the project
- the hard requirement is that the responsibilities are covered, not that a fixed workflow shape is copied every time

## 6. Mandatory Node Pack

The generated workflow must include these logical responsibilities. Names may vary, but responsibilities may not be omitted.

### 6.1 Infrastructure Nodes

1. `setup-realtime-infra`
   Responsibility:
   - websocket / long-connection setup
   - reconnect strategy assumptions
   - presence / fanout architecture baseline

2. `setup-push-infra`
   Responsibility:
   - APNs / FCM / desktop notification path
   - token registration and invalidation flow

3. `setup-media-pipeline`
   Responsibility:
   - upload path
   - object storage
   - thumbnail / transcoding / preview generation
   - access control

4. `setup-search-index`
   Responsibility:
   - message indexing
   - permission-filtered retrieval
   - deletion / recall propagation to index

### 6.2 Domain Logic Nodes

5. `implement-message-state-machine`
   Responsibility:
   - sent / delivered / read
   - ordering guarantees or ordering strategy
   - duplicate suppression / idempotency

6. `implement-sync-engine`
   Responsibility:
   - multi-device cursor sync
   - offline catch-up
   - reconnect reconciliation
   - unread count convergence

7. `implement-session-management`
   Responsibility:
   - multi-device sessions
   - device list
   - remote logout
   - suspicious session handling

8. `implement-moderation-controls`
   Responsibility:
   - mute / ban / remove
   - permission propagation
   - report / block / abuse hooks

### 6.3 Validation Nodes

9. `verify-message-state`
   Responsibility:
   - sent / delivered / read transitions
   - cross-device consistency

10. `verify-multi-device-sync`
    Responsibility:
    - phone ↔ desktop sync
    - reconnect recovery
    - unread count consistency

11. `verify-moderation-propagation`
    Responsibility:
    - admin actions reflected across client, server, and notifications

12. `verify-media-flow`
    Responsibility:
    - upload / preview / download / revoke access

## 7. Hard Acceptance Rules

For `im_realtime` projects, bootstrap-generated node-specs must embed these hard rules.

### Rule 1: Message state is mandatory

No IM workflow may be considered complete without explicit handling of:

- `sent`
- `delivered`
- `read`

If the product concept intentionally omits one of these, the node-spec must say so explicitly.

### Rule 2: Multi-device consistency is mandatory

If the concept includes multi-device login or desktop + mobile clients, node-specs must require:

- sync cursor behavior
- unread count convergence
- deletion / recall propagation
- session invalidation behavior

### Rule 3: Weak-network behavior is mandatory

Node-specs must include behavior for:

- disconnect
- reconnect
- duplicate delivery
- out-of-order replay
- offline catch-up

### Rule 4: Media is not just file upload

If media sending exists, node-specs must explicitly cover:

- storage
- preview / thumbnail / transcoding where relevant
- authorization
- message deletion / recall effects on media access

### Rule 5: Moderation must propagate

If groups/channels/admins exist, node-specs must cover:

- mute / ban / remove semantics
- permission cache invalidation
- UI feedback on affected clients
- auditability for admin actions

## 8. Node-Spec Contract Upgrade

For IM-specialized nodes, bootstrap must generate stronger node-specs.

Each node-spec must include:

1. `Goal`
2. `Input artifacts`
3. `Output artifacts`
4. `Cross-device invariants`
5. `Weak-network invariants`
6. `Failure modes to test`
7. `Downstream consumers`

### Research Requirement

Whenever the project has ambiguity, node-spec generation should prefer evidence from research over assumption.

Research sources may include:

- project README / docs / code structure
- upstream `.allforai/` artifacts
- external product references supplied by the user
- public product behavior patterns when browsing is available and appropriate

Rule:

- if the LLM can reduce uncertainty by researching the real product shape, it should do that instead of freezing a generic assumption into the node-spec

### Example: `implement-message-state-machine`

Required content:

- message identity model
- idempotency rule
- transition table
- retry / duplicate handling
- what counts as delivered
- what counts as read
- how state propagates to other clients

### Example: `verify-multi-device-sync`

Required content:

- at least one mobile -> desktop scenario
- at least one desktop -> mobile scenario
- reconnect scenario
- recall/delete propagation scenario
- unread count consistency scenario

## 9. Bootstrap Planning Changes

Step 3.5 should remain, but bootstrap should move more IM logic earlier.

### Before

- generic nodes generated first
- closure checks discover realtime/sync gaps later

### After

- IM detection triggers a research-assisted mandatory responsibility pack up front
- Step 3.5 still runs, but now mainly catches second-order omissions

This reduces avoidable re-planning.

## 9.1 Why Research Matters Here

Not all messaging products are Telegram.

Examples:

- customer-support chat
- gaming party chat
- enterprise secure messaging
- community channels
- creator broadcast tools

These products share IM traits but differ in:

- session model
- moderation depth
- retention rules
- media complexity
- delivery semantics
- search expectations

So bootstrap should:

- use research to determine which responsibilities are truly required
- use the mandatory IM pack only as a floor, not the full shape of the final workflow

## 10. Validation

The specialization is considered successful only if the generated workflow for an IM product includes:

- at least one realtime infra node
- at least one sync-specific node
- at least one message-state-specific node
- at least one IM-specific validation node

### Static checks

- workflow contains the mandatory logical responsibilities
- node-specs mention `workflow.json` consumers and outputs
- node-specs include cross-device and weak-network sections

### Thought-test checks

- Telegram-style scenario
- WhatsApp-style scenario
- Discord-style scenario

### Runtime checks

- bootstrap generates these nodes for an IM fixture
- generated run workflow executes without omitting IM-critical validation stages
- research-informed specialization chooses the right variant for different IM subtypes

## 11. Risks

### Risk 1: Over-triggering IM specialization

A support chat widget may not need the full Telegram-level node pack.

Mitigation:

- use severity tiers:
  - `im_light`
  - `im_realtime`
  - `im_platform`

Only `im_realtime` and above require the full pack.

### Risk 2: Too much node proliferation

Too many mandatory nodes may make workflows heavy.

Mitigation:

- allow node merging, but not responsibility removal
- validate logical responsibilities, not exact node names

### Risk 2.5: Over-hardcoding one IM archetype

If specialization is overfit to Telegram, the skill will perform badly on lighter or more regulated messaging products.

Mitigation:

- keep the mandatory pack at the responsibility level
- let research + LLM decide depth, split, and implementation strategy
- distinguish `im_light`, `im_realtime`, and `im_platform`

### Risk 3: Duplicate validation with Step 3.5

Mitigation:

- bootstrap handles first-order mandatory responsibilities
- Step 3.5 catches second-order closure gaps

## 12. Implementation Direction

1. Add IM specialization detection guidance to bootstrap.
2. Add a research-first specialization rule before mandatory pack injection.
3. Add mandatory IM node responsibilities.
4. Upgrade node-spec generation prompts for IM nodes.
5. Add Telegram thought-test as a regression artifact.
6. Add fixture or static validation that checks IM workflows contain the mandatory pack.

## 13. Decision

The issue is not that bootstrap fails to specialize at all.

The issue is that bootstrap currently generates **too-generic specialized skills** for realtime messaging systems.

For Telegram-class products, specialization must become:

- earlier
- harder
- more state-aware
- more validation-heavy

That is the required direction.
