# Codex host-command inheritance implementation plan

1. Add a standalone host-command module with strict option grammar, override
   validation, executable canonicalization, redaction, and injectable process readers.
2. Implement Linux procfs discovery and macOS native process-argv discovery with
   start-token race checks.
3. Replace the runner's hard-coded default template with discovered argv while
   retaining explicitly supplied legacy templates.
4. Add command provenance to state/report and update documentation.
5. Add parser, discovery, redaction, integration, and failure-path tests; run the
   focused suite and static checks.
6. Commit and push the completed change to `origin/main`.
