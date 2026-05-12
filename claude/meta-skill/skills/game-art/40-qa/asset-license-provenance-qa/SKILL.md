---
name: game-art-40-qa-asset-license-provenance-qa
description: Internal bundled meta-skill module for game-art/40-qa/asset-license-provenance-qa; use within generated bootstrap node-specs when this exact contract is selected.
---

# Asset License Provenance QA Skill

> Internal sub-skill for game-art pipelines. Status: bundled, inactive, not wired.

## Overview

Validates license, provenance, modification rights, commercial use, attribution,
and source evidence for existing assets or asset packs before they enter the art
pipeline.

This is a hard gate. Assets with unclear or failed license/provenance status
must not enter `engine-ready-art-output-contract`.

## Input Contract

Required: asset pack search results or user-provided asset manifest.

Optional: source strategy spec, license files, receipts, marketplace pages,
author/publisher metadata, attribution requirements, local asset paths, and
project license policy.

## Output Contract

Writes:

- `.allforai/game-design/art/sourcing/asset-license-provenance-qa-report.json`

License verdicts must include `candidate_id`, `asset_id`, `source_url`,
`source_platform`, `author_or_publisher`, `license_name`, `license_text_ref`,
`commercial_use_allowed`, `modification_allowed`, `redistribution_allowed`,
`attribution_required`, `attribution_text`, `receipt_or_proof_ref`,
`provenance_status`, `risk_level`, `status`, `repair_target`, and
`blocks_runtime`.

Allowed statuses: `passed`, `passed_with_attribution`, `needs_revision`,
`failed_license`, `failed_provenance`, `blocked_by_missing_evidence`.

Allowed risk levels: `low`, `medium`, `high`, `unknown`.

Downstream consumers: `existing-asset-adaptation-spec`,
`asset-pack-integration-qa`, `artifact-handoff-contract`,
`engine-ready-art-output-contract`, release/legal documentation, and runtime
implementation.

## Invocation Contract

```json
{
  "skill": "game-art/asset-license-provenance-qa",
  "mode": "validate",
  "input_paths": {
    "search_results": ".allforai/game-design/art/sourcing/asset-pack-search-results.json",
    "source_strategy": ".allforai/game-design/art/sourcing/asset-source-strategy-spec.json"
  },
  "output_root": ".allforai/game-design/art/sourcing"
}
```

Supported modes: `validate`, `validate_user_assets`, `repair_targets`.

## Automatic Validation

Check that every candidate has clear source, author/publisher, license evidence,
commercial-use status, modification rights, attribution rules, and proof of
purchase or allowed acquisition when required.

Hard gates:

- Unknown license cannot pass.
- Missing source/provenance cannot pass.
- Assets that cannot be modified cannot enter adaptation.
- Assets that cannot be used commercially cannot enter commercial game output.
- Attribution requirements must be preserved in the output contract.
- AI-generated or mixed-source packs must still document source terms.

State progression gates:

```text
passed
  license/provenance clear and no attribution blocker
passed_with_attribution
  usable only if attribution text is carried downstream
needs_revision
  evidence incomplete but repairable
failed_license
  license forbids required use
failed_provenance
  source or author cannot be verified
blocked_by_missing_evidence
  no license/proof/source evidence is available
```

Repair routing: missing evidence routes to search/user asset collection; license
conflicts route to `asset-source-strategy-spec`; attribution requirements route
to `engine-ready-art-output-contract`; adaptation rights failures block
`existing-asset-adaptation-spec`.

## Completion Conditions

Return `COMPLETED` when all selected assets have passed or
passed-with-attribution verdicts. Return `FAILED_VALIDATION` when any selected
runtime asset fails license/provenance gates.
