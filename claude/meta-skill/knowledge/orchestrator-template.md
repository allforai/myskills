# Orchestrator Template

> Used by bootstrap to generate .claude/commands/run.md in target projects.

## Generated run.md Structure

1. YAML frontmatter with name, description, arguments
2. Orchestrator loop protocol:
   - Read state-machine.json (ground truth)
   - Mechanically evaluate entry/exit_requires (call check_requires.py)
   - LLM decides next node (only when multiple choices or errors)
   - Dispatch subagent with node-spec
   - Compress result to <=500 char summary, write to state-machine.json
   - Safety checks (loop detection, progress monotonicity)
3. Diagnosis protocol reference (dispatch diagnosis subagent on failure)
4. Termination conditions

## Context Management

Orchestrator LLM context per iteration:
- Fixed: state-machine.json (nodes + safety + progress + node_summaries)
- Sliding: last 2-3 node results + last diagnosis (if any)
- Not in context: old node results, artifact contents, node-spec files

## Subagent Response Contract

All node subagents return:
```json
{
  "status": "success | failure | needs_input",
  "summary": "<=500 chars",
  "artifacts_created": [],
  "errors": [],
  "user_prompt": null
}
```
