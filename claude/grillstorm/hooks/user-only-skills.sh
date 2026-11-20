#!/bin/bash
# PreToolUse gate on the Skill tool: the skills listed below are user-invoked
# only. A user typing /name is expanded by the CLI and never reaches this hook;
# a model-side Skill tool call does, and is refused so the model cannot start
# these heavy, interactive flows on the user's behalf.
USER_ONLY="grillstorm"

input=$(cat)
# A payload this cannot read still lets the call through: refusing every Skill call because
# the payload shape changed would break the session. But it says so. A gate that stops
# working without a trace is one nobody knows to fix.
if ! skill=$(printf '%s' "$input" | python3 -c 'import sys, json
v = json.load(sys.stdin)["tool_input"]["skill"]
if not isinstance(v, str) or not v.strip():
    raise SystemExit(1)
print(v.rsplit(":", 1)[-1].strip())' 2>/dev/null); then
  echo "user-only-skills: could not read the Skill tool payload; the user-only gate did not run for this call." >&2
  exit 0
fi

for name in $USER_ONLY; do
  if [ "$skill" = "$name" ]; then
    echo "/$name is user-invoked only. Do not start it yourself; tell the user the command exists and let them type /$name." >&2
    exit 2
  fi
done
exit 0
