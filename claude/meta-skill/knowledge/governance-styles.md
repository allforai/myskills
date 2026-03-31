# Governance Styles & Operation Profiles

> Extracted from product-design-skill: product-concept.md (Step 3 Phase A.5), product-map.md

---

## A. 4 Governance Styles

Every product has business flows that need governance decisions. Different flows within the same product may use different styles. The governance style directly determines downstream screens, roles, and system boundaries.

### 1. Strict Pre-Review (strict_prereview)

**What it is**: Operations must be reviewed/approved before taking effect.

**When to apply**:
- Financial operations (payments, withdrawals, refunds)
- Content with legal/compliance risk (regulated industries)
- Permission changes (role assignments, access grants)
- First-time operations by new/unverified users

**Downstream implications**:
- **Screens needed**: Review queue screen, review status tracking, reviewer dashboard
- **Roles needed**: Reviewer/approver role with dedicated workflow
- **System boundary**: Registration/onboarding collects complete qualification information upfront
- **Use cases**: Approval flows, rejection with reason, re-submission after rejection

### 2. Loose Post-Hoc (loose_posthoc)

**What it is**: Operations take effect immediately. Problems are handled after the fact.

**When to apply**:
- Low-risk content operations (social posts, comments)
- Marketplaces where speed matters more than curation
- Internal tools where users are trusted professionals

**Downstream implications**:
- **Screens needed**: Report/complaint channels, violation records, automated monitoring dashboard
- **Roles needed**: Moderation/compliance role (reactive, not gatekeeping)
- **System boundary**: Registration is minimal (invite code + basic info only); complex verification is external or deferred
- **Use cases**: Report handling, violation escalation, content takedown

### 3. Graduated (graduated)

**What it is**: First-time operations require strict review; as reputation accumulates, operations auto-approve.

**When to apply**:
- Content publishing platforms (listings, reviews, advertisements)
- Marketplace seller management
- Any scenario where trust builds over time

**Downstream implications**:
- **Screens needed**: Reputation score system, graduated rule configuration, trust level dashboard
- **Roles needed**: Initial reviewer + system admin for rule configuration
- **System boundary**: Hybrid -- strict initially, progressively relaxed
- **Use cases**: First submission review, reputation threshold configuration, auto-approval rules

### 4. Auto-Review (auto_review)

**What it is**: AI/rules automatically judge; only anomalies trigger human intervention.

**When to apply**:
- High-volume content moderation
- Standardized compliance checks
- Pattern-matching violations (spam, fraud signals)

**Downstream implications**:
- **Screens needed**: Rule engine configuration, anomaly queue, false positive review
- **Roles needed**: Rule administrator + exception handler
- **System boundary**: Rule engine is in-scope; edge cases escalate to human review
- **Use cases**: Rule creation/editing, anomaly triage, false positive correction

### Governance Style Schema

```json
"governance_styles": [
  {
    "flow_domain": "Content publishing",
    "style": "auto_review",
    "rationale": "First-time human review, auto-approve after reputation builds",
    "downstream_implications": ["Need reputation scoring system", "Need auto-review rule configuration"],
    "system_boundary": {
      "in_scope": ["Content editing and submission", "Review status display"],
      "external": ["Identity verification (third-party KYC)"]
    }
  }
]
```

### Concept Baseline Representation

In `concept-baseline.json`, governance styles are stored compactly:

```json
"governance_styles": [
  {
    "flow_domain": "Content publishing",
    "style": "auto_review",
    "system_boundary": {
      "in_scope": ["Content editing and submission"],
      "external": ["Identity verification"]
    }
  }
]
```

Downstream phases that need full detail (like `downstream_implications` and `rationale`) pull from `product-mechanisms.json` directly.

---

## B. Operation Profiles

Per-role frequency model that determines screen granularity and interaction design. Derived from role characteristics (impl_group, app, platform), not from preferences.

### 3 Operation Profile Types

| Profile | Frequency Model | Typical Role | Screen Granularity |
|---------|----------------|-------------|-------------------|
| **High-freq, few-ops** | Frequent usage, short sessions, few operations per visit | End user on mobile | `single_task_focus` -- each screen focuses on one task, deep navigation, minimize jump layers |
| **Mid-freq, mid-ops** | Daily usage, moderate session length, multiple operations | End user on desktop OR service provider | `multi_function_per_page` (provider) or moderate aggregation (desktop end-user) |
| **Low-freq, heavy-ops** | Infrequent usage, long sessions, many operations per visit | Admin/back-office | `dashboard_workbench` -- KPI overview + task queue + batch operations; deep nesting for config |

### Derivation Rules

| Role Characteristic | Operation Profile | Screen Granularity Guidance |
|--------------------|------------------|---------------------------|
| End user (end_user) + mobile | High-freq few-ops, short attention, single-hand use | Each screen focuses single task, deep navigation, minimize jump layers |
| End user (end_user) + desktop | Mid-freq mid-ops, multi-tab browsing | Moderate aggregation of related features, sidebar-assisted navigation |
| Service provider (provider) + desktop | Mid-freq many-ops, daily operations, efficiency first | **Same-page multi-function**: list + detail + actions in same view, reduce page jumps. Frequent actions front-loaded, infrequent actions collapsed |
| Admin (admin) + desktop | Low-freq heavy-ops, review/config/monitoring | **Dashboard + workbench**: KPI overview + pending queue + batch operations. Config can be deeply nested |

### 80/20 Rule Application

For each role, identify the top 20% high-frequency operations (derived from core jobs + daily operation scenarios). These operations must be reachable within 1-2 clicks. The remaining 80% can be nested deeper.

Product-map generates `business-flows` which can further validate and refine the 80/20 split.

### Operation Profile Schema

```json
{
  "role_id": "R2",
  "role_name": "Service provider backend user",
  "impl_group": "provider",
  "app": "provider",
  "operation_profile": {
    "frequency": "medium",
    "density": "high",
    "screen_granularity": "multi_function_per_page",
    "high_frequency_tasks": ["Ticket processing", "Resource management", "Message reply"],
    "design_principle": "Same-page multi-function, frequent actions front-loaded, list+detail+actions in same view"
  }
}
```

### Screen Granularity Impact on Design

| Dimension | multi_function_per_page (Backend) | single_task_focus (Frontend) |
|-----------|----------------------------------|----------------------------|
| Same-entity CRUD | **One screen**: list + create modal + detail panel + inline actions | **Multiple screens**: list -> detail -> edit, page navigation |
| Create operation | Same-page modal/drawer, don't leave list context | Independent full-screen form page |
| Detail view | Sidebar panel, list still visible | Independent full-screen detail page |
| Batch operations | Checkbox + batch action bar (bulk delete/export/status change) | Uncommon, item-by-item operations |
| Navigation | Sidebar menu, main area content switching, rarely full-page jumps | Deep navigation (enter -> back), bottom tab switching |
| Data density | High-density tables, multi-column, compact layout | Low-density cards, emphasis on whitespace and visual hierarchy |

### Consumer vs Professional Interaction Design

| Dimension | Frontend (consumer) | Backend (professional) |
|-----------|-------------------|---------------------|
| Information density | Low-to-medium, clear visual hierarchy, but allows contextual aggregation | High -- compact tables, multi-column, data-dense |
| Guidance level | Strong -- step guidance, empty state hints, operation confirmations | Weak -- assume user knows the business, minimize confirmation dialogs |
| Page granularity | Aggregated by user intent (see information density spectrum) | Coarse -- same-page multi-function, one page manages all operations for one entity |
| Operation style | Explicit -- large buttons, clear CTA, gesture navigation | Implicit -- inline editing, right-click menus, keyboard shortcuts, batch operations |
| Error tolerance | Strict -- irreversible operations get multi-confirmation, auto-save | Lenient -- trust user judgment, quick undo rather than repeated confirmation |
