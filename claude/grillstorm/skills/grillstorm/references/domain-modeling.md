# Domain Modeling Protocol

Actively build and sharpen the project's domain model while grilling. Challenge fuzzy
terms, invent concrete edge cases, compare claims with code, and record language and
important decisions as soon as they crystallize.

## Locate the context

Most repositories use one root `CONTEXT.md`. If `CONTEXT-MAP.md` exists, use it to locate
multiple bounded contexts and their relationships. Create context files lazily, only when
the first project-specific term is resolved.

## During the session

- Challenge conflicts with existing glossary language immediately.
- Replace vague or overloaded words with one precise canonical term.
- Use concrete scenarios to probe boundaries and relationships.
- Check stated behavior against the code; surface contradictions as decisions.
- Update the relevant `CONTEXT.md` immediately after resolving a term.

`CONTEXT.md` is a glossary, not a spec. Keep implementation details out.

Use this compact format:

```markdown
# <Context Name>

<One or two sentences describing the context.>

## Language

**Order**:
The customer's accepted request for goods or services.
_Avoid_: Purchase, transaction
```

Definitions are one or two sentences. Include only project-specific concepts. Pick one
preferred word and list discouraged synonyms under `_Avoid_`.

For multiple contexts, keep a root map:

```markdown
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) - receives and tracks orders
- [Billing](./src/billing/CONTEXT.md) - invoices and processes payment

## Relationships

- **Ordering -> Billing**: Ordering emits `OrderAccepted`; Billing consumes it.
```

## ADRs

Offer an ADR only when all three conditions hold:

1. The decision is meaningfully expensive to reverse.
2. A future reader would find it surprising without context.
3. Genuine alternatives were considered and a tradeoff was chosen.

Store ADRs under `docs/adr/` with the next sequential number:

```markdown
# <Short decision title>

<One to three sentences stating the context, decision, and reason.>
```

Add status, alternatives, or consequences only when they add real value. Create the ADR
directory lazily.
