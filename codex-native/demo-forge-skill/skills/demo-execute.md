# Demo Execute For Codex Native

Use this workflow to generate and inject demo data into the target application.

## Objectives

- generate deterministic records from the approved plan
- preserve entity relationships
- populate the target system by API or database strategy
- log chain failures and partial completion explicitly

## Outputs

- `.allforai/demo-forge/forge-data-draft.json`
- `.allforai/demo-forge/forge-data.json`
- `.allforai/demo-forge/forge-log.json`

## Completion standard

- records were actually generated
- injected data is not silently partial
- failures are logged with enough context for rerun or repair
