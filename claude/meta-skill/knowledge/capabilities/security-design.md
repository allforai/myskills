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

## Composition Hints

### Single Node (default)
One security-design node covers threat modeling + mechanism selection for the entire project.

### Merge with Infrastructure
For simple projects (single web app, no E2E encryption): merge security decisions into infra-design.

### Skip Entirely
For internal tools with no user data, local-only CLI tools, or prototype/hackathon projects where security is explicitly deferred.
