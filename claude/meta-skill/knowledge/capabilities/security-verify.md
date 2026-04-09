# Security Verify Capability

> Verify that security design decisions are actually implemented in code.
> Runtime counterpart of security-design: design says "use JWT auth on all endpoints",
> this capability checks if auth middleware is actually applied.

## Goal

After implementation, verify that security measures declared in security-design
artifacts are present in the codebase. Catches the gap between "we decided to do X"
and "the code actually does X".

## Prerequisites

1. security-design artifacts exist (security-design.json or security-design.md)
2. Implementation is complete (code exists to verify)

## What LLM Must Accomplish (not how)

### Required Outputs

| Output | What |
|--------|------|
| `security-verify-report.json` | Per-decision verification: implemented / missing / partial |

**security-verify-report.json field schema:**
```json
{
  "decisions_checked": [
    {
      "decision": "<string — from security-design>",
      "category": "<enum: auth | authorization | encryption | rate_limiting | input_validation | key_management>",
      "status": "<enum: implemented | missing | partial>",
      "evidence": "<string — file:line if implemented, 'missing' if not>",
      "risk": "<enum: critical | high | medium | low>"
    }
  ],
  "summary": {
    "total_decisions": "<number>",
    "implemented": "<number>",
    "missing": "<number>",
    "partial": "<number>",
    "critical_missing": "<number>"
  }
}
```

### Check Dimensions

**1. Authentication Coverage**
- Every non-public API endpoint has auth middleware/guard
- Token lifecycle is implemented (issue, refresh, revoke, expiry)
- Auth bypass: no endpoint accidentally skips auth (check route registration)

**2. Authorization Enforcement**
- Role-based access: each role can only access permitted endpoints
- Resource-level access: users can only access their own data (no IDOR)
- Admin routes are separated and additionally protected

**3. Encryption Implementation**
- Transport: TLS configured (HTTPS enforced, no HTTP fallback)
- At-rest: sensitive fields encrypted in DB (if security-design requires)
- E2E: end-to-end encryption implemented (if security-design requires)

**4. Rate Limiting**
- Rate limiter configured on public endpoints
- Per-user and per-IP limits set
- Rate limit headers returned (X-RateLimit-Remaining)

**5. Input Validation**
- Request body validation on all mutation endpoints (POST/PUT/PATCH)
- SQL injection protection (parameterized queries, no string concatenation)
- XSS protection (output encoding, CSP headers for web)

**6. Key Management**
- No hardcoded secrets in source code (scan for API keys, passwords in code)
- Secrets loaded from environment variables or secret manager
- .env files in .gitignore

### Required Quality

- Every decision from security-design has an explicit verdict
- Critical missing items (auth bypass, no encryption on sensitive data) flagged as critical risk
- Evidence is file:line based, not self-reported
- No silent skips — every decision must be checked

## Methodology Guidance (not steps)

- **Decision-driven**: Read security-design artifacts first, then verify each decision against code
- **Code scanning**: For auth coverage, trace from route registration → middleware chain → handler
- **Negative testing**: Try to find paths that bypass security (unprotected routes, missing validation)
- **Secret scanning**: Grep for common secret patterns (API_KEY=, password=, Bearer hardcoded tokens)

## Knowledge References

### Phase-Specific:
- cross-phase-protocols.md §Safety: security-related safety rules

## Composition Hints

### Single Node (default)
One security-verify node runs after all implementation completes, alongside or after product-verify.

### Merge with Quality Checks
For simple projects: add security checks as an additional dimension within quality-checks.

### Skip Entirely
For internal tools with no user data, prototype projects, or when security-design was explicitly skipped.
