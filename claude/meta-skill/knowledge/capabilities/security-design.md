# Security Design Capability

> Design security architecture: authentication, authorization, encryption,
> rate limiting, input validation, key management.
> Internal execution is LLM-driven — security posture adapts to project threat model.

## Goal

Identify security requirements, perform lightweight threat modeling, select
appropriate security mechanisms, and produce a security architecture document
that implementation and verification nodes consume.

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `security-design.json` | Security decisions: auth scheme, encryption approach, threat mitigations |
| `security-design.md` | Human-readable security architecture document |

### Design Dimensions (LLM selects which apply)

| Dimension | Options to evaluate | Applies when |
|-----------|-------------------|-------------|
| Authentication | JWT / OAuth2 / SSO / 2FA / Passkeys / API keys | Product has user accounts |
| Authorization | RBAC / ABAC / permission matrix / row-level security | Product has multiple roles |
| Transport encryption | TLS / mTLS | Always (HTTPS minimum) |
| End-to-end encryption | Signal Protocol / MLS / custom | Product handles sensitive private communication |
| Data-at-rest encryption | DB-level / application-level / KMS-managed | Product stores PII or financial data |
| Rate limiting | Token bucket / sliding window / per-user / per-IP | Product has public API or user-facing endpoints |
| Input validation | Schema validation / sanitization / parameterized queries | Always (OWASP Top 10) |
| Key management | Environment vars / HashiCorp Vault / cloud KMS / keychain | Product uses API keys, encryption keys, or secrets |

### Required Quality

- Threat model covers at least the STRIDE categories relevant to the project
- Every authentication flow has a defined token lifecycle (issue, refresh, revoke)
- Sensitive data paths are identified (PII, credentials, payment data) with protection measures
- OWASP Top 10 mitigations are addressed for the project's tech stack

## Interaction Mode

**Search-driven selection questions (mandatory for auth, authorization, and encryption dimensions):**

For each design dimension where multiple viable options exist, LLM MUST:

1. **WebSearch** 1-2 rounds: security best practices, real-world breach case studies, and framework ecosystem support for the candidate approaches
2. **Present 2-4 options** as a selection question, each with:
   - Approach name + one-line positioning (e.g., "Passkeys — phishing-resistant, no password to leak, WebAuthn standard")
   - Evidence from search ("Apple/Google adopted 2023, 40% faster login in Kayak case study")
   - Fit assessment for THIS project ("your app has mobile + web clients — Passkeys need fallback for older Android")
3. **User selects** — LLM does NOT decide for the user
4. **"Other" response** → WebSearch with user's input → new selection question with refined options

**When to skip interaction:**
- Dimension has an industry-standard default with no meaningful tradeoff (e.g., TLS for transport, parameterized queries for SQL injection)
- User already specified the approach in bootstrap or product-concept
- **Decision already made in product-concept tech-architecture sub-phase** — load `tech-architecture.json` and inherit those choices. Only ask about implementation details (token lifecycle, key rotation policy), not the mechanism selection itself.
- In these cases, state the decision with rationale and move on (user can override)

## Methodology Guidance (not steps)

- **STRIDE threat modeling**: For each component, consider Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege
- **OWASP Top 10**: Map to the project's specific tech stack (e.g., SQL injection for relational DB, XSS for web frontend)
- **Zero Trust principle**: Don't trust internal networks — authenticate and authorize every request
- **Least privilege**: Every component gets minimum permissions needed
- **Defense in depth**: Multiple layers of protection, not a single perimeter

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Safety: security-related safety rules
- defensive-patterns.md: fallback and error handling that doesn't leak information

## Downstream Consumers

> Bootstrap reads this table to generate Context Pull sections for downstream node-specs.
> `required` = subagent reports error if file missing; `optional` = warning + continue.

| Artifact | Field Path | Consumer Capability | Required | Reason |
|----------|------------|---------------------|----------|--------|
| `security-design.json` | auth scheme, token lifecycle | translate (implement nodes) | required | 实现需要知道用什么认证方案（JWT/OAuth/Passkeys） |
| `security-design.json` | authorization model | translate (implement nodes) | required | 实现需要知道权限模型（RBAC/ABAC）来写 middleware |
| `security-design.json` | all decisions | security-verify | required | security-verify 逐项对照安全决策与实现 |
| `security-design.json` | rate limiting config | translate (implement nodes) | optional | 缺失时按默认限流策略继续 |

## Composition Hints

### Single Node (default)
One security-design node covers threat modeling + mechanism selection for the entire project.

### Merge with Infrastructure
For simple projects (single web app, no E2E encryption): merge security decisions into infra-design.

### Skip Entirely
For internal tools with no user data, local-only CLI tools, or prototype/hackathon projects where security is explicitly deferred.
