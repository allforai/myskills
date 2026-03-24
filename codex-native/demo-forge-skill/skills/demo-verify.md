# Demo Verify For Codex Native

Use this workflow to verify that demo data, media, and business flows actually
work in the running application.

## Objectives

- verify page and flow rendering
- verify media integrity
- verify list/detail/business-chain realism
- classify failures by routing owner

## Outputs

- `.allforai/demo-forge/verify-report.json`
- `.allforai/demo-forge/verify-issues.json`
- `.allforai/demo-forge/screenshots/`

## Native rules

- do not claim verification succeeded if browser automation was unavailable
- route issues into design, media, execute, or development buckets
- preserve the 95 percent pass-rate goal after excluding deferred development
  issues
