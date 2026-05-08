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
| Transport encryption | TLS (one-way, client verifies server) / mTLS (mutual, both sides present certs — standard for gRPC service-to-service) | Always (HTTPS minimum). For gRPC microservices: evaluate mTLS for inter-service communication; requires CA setup, certificate provisioning per service, and rotation policy. |
| End-to-end encryption | Signal Protocol (Double Ratchet + X3DH) / MLS (Messaging Layer Security — designed for large groups) / custom | Product handles sensitive private communication. **Key distribution server is a new attack surface**: in X3DH, the server distributes prekey bundles — a compromised server can perform prekey substitution attacks. Signed prekeys (authenticated with long-term identity key) are mandatory, not optional. **Multi-device trust model** must be explicitly decided: (a) Each device has independent keys — losing a device loses message history; (b) Key backup encrypted to user master secret — usability vs security tradeoff. **Group E2E encryption**: Signal Protocol's pairwise design does not scale to large groups; MLS (RFC 9420) is designed for groups. Decide the group size threshold where MLS replaces Signal. |
| Data-at-rest encryption | DB-level / application-level / KMS-managed | Product stores PII or financial data |
| Rate limiting | Token bucket / sliding window / per-user / per-IP | Product has public API or user-facing endpoints |
| Input validation | Schema validation / sanitization / parameterized queries | Always (OWASP Top 10) |
| Key management | Environment vars / HashiCorp Vault / cloud KMS / **macOS Keychain (required for macOS/iOS native apps)** / Android Keystore | Product uses API keys, encryption keys, or secrets. For macOS/iOS: Keychain is the REQUIRED storage — UserDefaults is plaintext and env vars are unavailable in sandboxed bundles. |
| Regulatory / Compliance | GDPR (EU user data) / COPPA (under-13 users) / PCI-DSS (payment card data) / HIPAA (health data) / App Store guidelines | Product collects personal data, handles payments, or targets minors |
| Game anti-cheat | Server-side authoritative validation / replay verification / anomaly detection / ban system | Multiplayer games or games with economy systems — client-side data must never be trusted for score/inventory/currency |
| Electron IPC security | `contextBridge` with explicit allowlist / `contextIsolation: true` / `nodeIntegration: false` / `sandbox: true` / IPC channel validation | All Electron desktop apps — renderer process must not have direct Node.js access |
| Tauri v2 Capabilities | Fine-grained IPC permission scopes in `src-tauri/capabilities/*.json` (command allowlist per capability, scope-limited by path/host) | All Tauri v2 apps — least-privilege capability set required |
| IDE Plugin data access | Obsidian: full Node.js + vault access (no sandbox) — document which vault data the plugin reads/writes, and whether it transmits data externally; secrets via `app.vault.adapter` local storage, NOT source code. VS Code: extension host process (not sandboxed) — use `vscode.SecretStorage` for secrets (OS Keychain/Credential Manager), declare minimum `activationEvents`, avoid requesting `workspace` access unless needed | All Obsidian plugins and VS Code extensions — no granular permission model exists in either IDE; plugin README must explicitly state data access scope |
| Bot webhook security | Telegram: verify `X-Telegram-Bot-Api-Secret-Token` header on all webhook requests (configure via `setWebhook?secret_token=`); bot token never logged or committed. Slack: verify `X-Slack-Signature` HMAC-SHA256 on all requests (Bolt does this automatically; custom servers must implement manually); OAuth scopes minimized to principle of least privilege. Discord: verify `X-Discord-Signature` (`ed25519` public key signature). All bots: rate-limit commands per user/channel; token rotation policy documented; GDPR data retention policy if storing user messages | All Discord/Slack/Telegram bot projects — bot tokens are high-value targets; webhook handlers must verify request origin or attackers can inject arbitrary commands |

### Required Quality

- Threat model covers at least the STRIDE categories relevant to the project
- Every authentication flow has a defined token lifecycle (issue, refresh, revoke)
- Sensitive data paths are identified (PII, credentials, payment data) with protection measures
- OWASP Top 10 mitigations are addressed for the project's tech stack
- **HarmonyOS/ArkTS apps**: HUKS (Harmony Unified Key Store `@ohos.security.huks`) is the required secure key storage. Do NOT use `@ohos.data.preferences` (plaintext key-value) for secrets. Configure HUKS key policy with: `HuksKeyPurpose.ENCRYPT_DECRYPT`, restricted algorithm, and unlock-required access control equivalent. All system resource permissions (camera, mic, location) MUST be declared in `module.json5` `requestPermissions[]`.
- **macOS/iOS apps**: Keychain access group configuration is documented with STRIDE analysis (Elevation of Privilege: wrong access group allows cross-app secret reads; Tampering: unrestricted Keychain items survive app uninstall and are accessible to reinstalled apps). Key items: `kSecAttrAccessible` value should be `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` for most secrets (not `kSecAttrAccessibleAlways`).

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
