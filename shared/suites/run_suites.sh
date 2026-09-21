#!/usr/bin/env bash
# Runs every line of shared/suites/suites.txt as its own pytest invocation. Keeps going after a failure so one
# red suite does not hide another, and exits non-zero if any line failed.
set -uo pipefail
cd "$(dirname "$0")/../.."

status=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|'#'*) continue ;; esac
  echo "[suites] $line"
  # Word splitting is intended: a line may name several test files.
  # shellcheck disable=SC2086
  env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX \
    python3 -B -m pytest -q -p no:cacheprovider $line || { echo "[suites] FAILED: $line" >&2; status=1; }
done < shared/suites/suites.txt
exit "$status"
