# IM Realtime Specialization (Codex)

> Codex-only specialization guidance for Telegram / WhatsApp / Discord / secure messaging style products.
> Use this as a responsibility-floor, not as a fixed workflow template.

## Principle

For IM products, bootstrap should follow this order:

1. **Research first**
   Read product docs, code, upstream `.allforai/` artifacts, and any user-supplied references.
2. **LLM synthesis second**
   Let the model infer the workflow shape from evidence.
3. **Mandatory responsibility pack third**
   If the project is truly `im_realtime`, inject the minimum responsibility set below.

This prevents two failure modes at once:

- over-hardcoding Telegram into every chat-adjacent project
- under-planning the hidden complexity of realtime messaging systems

## Detection Signals

Treat a project as `im_realtime` when product language and feature signals strongly match:

### Product-language signals

- chat
- messaging
- telegram
- direct message
- group chat
- channel
- online status
- read receipt
- multi-device sync

### Feature signals

- one-to-one messaging
- group chat
- message delivery/read states
- media sending
- message deletion or recall
- mute / notification preferences
- multi-device login
- moderation / admin actions

### Technical signals

- websocket / socket / realtime transport
- push notifications
- offline sync
- object storage / CDN
- search indexing

## Mandatory Responsibility Pack

These are mandatory **responsibilities**, not mandatory exact node names.
LLM may merge or split them, but may not omit them.

### Infrastructure

- realtime transport
- push delivery path
- media storage / processing
- search indexing

### Domain logic

- message state machine
- sync engine
- session management
- moderation controls

### Validation

- message-state verification
- multi-device sync verification
- moderation propagation verification
- media flow verification

## Hard Rules

### Rule 1: Message state is first-class

The workflow must explicitly account for:

- sent
- delivered
- read

If any state is intentionally omitted, node-specs must say so explicitly.

### Rule 2: Weak-network behavior is required

Node-specs must cover:

- disconnect
- reconnect
- duplicate delivery
- offline catch-up
- out-of-order replay

### Rule 3: Cross-device consistency is required

If the concept includes more than one client or session type, node-specs must cover:

- unread convergence
- recall/delete propagation
- cursor sync
- remote logout / session invalidation

### Rule 4: Media is not just upload

If media exists, node-specs must include:

- storage
- preview / thumbnail / transcoding where relevant
- access control
- delete / recall impact

### Rule 5: Moderation must propagate

If groups/channels/admin roles exist, node-specs must include:

- mute / ban / remove semantics
- permission propagation
- UI feedback across clients
- report / block hooks when relevant

## Node-Spec Upgrade

For IM-specialized nodes, generated node-specs should include:

- input artifacts
- output artifacts
- cross-device invariants
- weak-network invariants
- failure modes to test
- downstream consumers

## Non-Goal

Do not force every messaging product into a Telegram-sized workflow.

Use the mandatory pack as a floor for `im_realtime`, not as a universal shape for:

- support chat widgets
- comment systems
- lightweight in-app chat
