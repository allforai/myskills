#!/bin/bash
# PreToolUse gate on the Skill tool: the skills listed below are user-invoked
# only. A user typing /name is expanded by the CLI and never reaches this hook;
# a model-side Skill tool call does, and is refused so the model cannot start
# these heavy, interactive flows on the user's behalf.
USER_ONLY="bootstrap setup"

input=$(cat)
skill=$(printf '%s' "$input" | python3 -c 'import sys, json
try:
    v = json.load(sys.stdin).get("tool_input", {}).get("skill", "")
except Exception:
    v = ""
print(str(v).rsplit(":", 1)[-1].strip())' 2>/dev/null)

for name in $USER_ONLY; do
  if [ "$skill" = "$name" ]; then
    echo "/$name is user-invoked only. Do not start it yourself; tell the user the command exists and let them type /$name." >&2
    exit 2
  fi
done
exit 0
