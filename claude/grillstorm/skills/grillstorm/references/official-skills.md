# Official Skill Invocation

Grillstorm orchestrates installed Matt Pocock skills. Their inner disciplines stay
authoritative. This file only says which skill to load, when, and what Grillstorm owns
after they return.

## Resolve by name

Look up the skill registry for these exact names. On Claude Code they may appear as
`mattpocock-skills:<name>`. On Codex and Pi they are the bare name. Do not inspect a
fixed cache path. Do not substitute Grillstorm reference files for a missing official
skill.

| Role | Official name | Required when |
|---|---|---|
| Setup | `setup-matt-pocock-skills` | `docs/agents/` is missing or invalid |
| Grill | `grilling` | every design interview |
| Grill + docs | `grill-with-docs` | a software change that should update glossary/ADRs |
| Alias | `grill-me` | never as a protocol; it only launches `grilling` |
| Spec | `to-spec` | the route publishes a spec |
| Tickets | `to-tickets` | `ticketed` or `program` |
| TDD | `tdd` | execution of approved work |
| Review | `code-review` | after each verified work unit and at global close |
| Diagnose | `diagnosing-bugs` | a hard bug during implementation or a check |
| Research | `research` | an external fact is an unsettled prerequisite |
| Prototype | `prototype` | a design question needs a throwaway artifact |
| Depth | `codebase-design` | module depth, interface, or seam placement is itself in question |
| Conflicts | `resolving-merge-conflicts` | an actual merge/rebase conflict exists |

If a required skill is missing, do not substitute a Grillstorm file. Run
`python3 scripts/install_official_skills.py status` from this skill directory, then ask
once:

> Official Matt Pocock skills are missing: <names>. Install them now? Recommended: **yes**.

On **yes**, run `python3 scripts/install_official_skills.py install` and follow its printed
command. After a successful install, load each official `SKILL.md` from the paths the
script reports. Do not wait for a session restart. If the installer fails or names remain
missing, print the command and stop.

On **no**, stop. Do not continue the Grillstorm run.

Never invoke official `implement`. Official `grilling`, `grill-me`, and `grill-with-docs`
are design-phase only.

## Design-phase questions

Official design skills may ask. Follow their questions, seam checks, shared-understanding
confirmations, and ticket quizzes. Persist every accepted answer under
`docs/grillstorm/<goal-slug>/` immediately.

When recording an accepted decision, also apply the purpose-chain rules in
`orientation-and-intent.md`: intent before mechanism, smallest purpose-complete option,
source `evidence_verified` or `user_confirmed`.

## Execution-phase silence

After the launch contract is frozen:

- load official `tdd`, `code-review`, and `diagnosing-bugs` only when their trigger exists;
- do not load `grilling`, `grill-me`, `grill-with-docs`, `to-spec`, or `to-tickets`;
- do not invoke official `implement`;
- unforeseen in-scope choices adopt the recommended option inside launch authority.

## Host loading

Read the official `SKILL.md` (or invoke the namespaced skill) and follow it for that stage.
Then return to this Grillstorm skill for routing, local artifacts, DAG, concurrency, and
resume.
