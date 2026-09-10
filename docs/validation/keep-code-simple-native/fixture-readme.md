# Lantern reports (synthetic review fixture)

This local fixture has three independent business areas. It has no real customers, credentials, network clients or payment gateway.

- Catalog: export rows as CSV, preserving commas, quotes and newlines inside fields. Existing exports use the shared `write_csv` interface.
- Search: normalize a user query by trimming outside whitespace and lowercasing it. Internal whitespace remains meaningful.
- Billing: one invoice may be collected once. A retry with the same request key returns the prior receipt rather than charging again. A collection is recorded for later reconciliation. Money and record integrity are business requirements regardless of frequency or amount.

The sources and tests are intentionally small. There are no usage metrics. The `src/tests/test_contracts.py` test file writes a marker if executed so the native review exercise can detect accidental test execution. Read it as evidence; the simplicity review must not execute it.

No dependencies beyond Python's standard library. `src/` is the review scope. Output goes only under `docs/keep-code-simple/`; do not change this fixture's sources or requirements.
