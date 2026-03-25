# Codex Smoke Run Template

Use this template for each real Codex smoke run.

Recommended order:

1. `codex-test-project3-replication.md`
2. `codex-test-project2-teampulse.md` (`code-tuner` section first)
3. `codex-test-project5-markethub-demo.md`
4. `codex-test-project4-pulsecrm-ui.md`
5. `codex-test-project1-fresheats.md`

---

## Run Record

### Metadata

- Date:
- Operator:
- Prompt:
- Plugin(s):
- Project directory:
- Codex version / environment:

### Scope

- Full prompt or partial prompt:
- If partial, which section:

### Preconditions

- Required upstream artifacts present: `yes | no`
- Runtime/app URL available: `yes | no | not needed`
- Credentials available: `yes | no | not needed`
- External tools available:
  - Playwright:
  - Search:
  - OpenRouter / XV:
  - Image generation:
  - Video generation:

### Execution Summary

- Result: `PASS | FAIL | PARTIAL | BLOCKED`
- Stop phase:
- Total blockers:
- Total warnings:

### Expected Artifacts Check

| Artifact | Expected | Found | Notes |
|----------|----------|-------|-------|
| example | yes | yes | |

### Quality Gate Check

| Check | Expected | Actual | Pass? |
|------|----------|--------|-------|
| example | `20+ tasks` | `24` | yes |

### Prompt vs Implementation Notes

- Any mismatch between prompt and current implementation:
- Any ambiguous artifact contract:
- Any phase naming mismatch:

### Plugin Behavior Notes

- What worked as expected:
- What was surprising:
- What appears brittle:

### Fixes Needed

- Prompt fix:
- Doc fix:
- Implementation fix:
- None:

### Final Assessment

- Confidence after this run: `high | medium | low`
- Can this prompt be reused as regression smoke: `yes | no | after fixes`
- Next recommended run:
