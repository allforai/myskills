#!/usr/bin/env bash
set -euo pipefail

plugin_source="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
grok_base="${GROK_HOME:-${HOME}/.grok}"
plugin_dest="${grok_base}/plugins/megastorm"
dry_run=0

while (($#)); do
  case "$1" in
    --dry-run) dry_run=1; shift ;;
    --dest)
      [[ $# -ge 2 ]] || { echo "--dest requires an absolute path" >&2; exit 2; }
      plugin_dest="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[[ "${plugin_dest}" = /* ]] || { echo "destination must be absolute" >&2; exit 2; }
[[ -f "${plugin_source}/.claude-plugin/plugin.json" ]] || {
  echo "source plugin manifest is missing" >&2; exit 1;
}
[[ -f "${plugin_source}/skills/megastorm/SKILL.md" ]] || {
  echo "Megastorm skill is missing" >&2; exit 1;
}
[[ -f "${plugin_source}/skills/cross-exam/SKILL.md" ]] || {
  echo "Cross-exam skill is missing" >&2; exit 1;
}

if ((dry_run)); then
  echo "Would install ${plugin_source} -> ${plugin_dest}"
  exit 0
fi

mkdir -p "$(dirname "${plugin_dest}")"
staging="${plugin_dest}.staging.$$"
trap 'rm -rf "${staging}"' EXIT
rm -rf "${staging}"
cp -R "${plugin_source}" "${staging}"
if [[ -e "${plugin_dest}" ]]; then
  backup="${plugin_dest}.previous.$$"
  mv "${plugin_dest}" "${backup}"
  if ! mv "${staging}" "${plugin_dest}"; then
    mv "${backup}" "${plugin_dest}"
    exit 1
  fi
  rm -rf "${backup}"
else
  mv "${staging}" "${plugin_dest}"
fi
trap - EXIT

echo "Installed Megastorm and Cross-exam to ${plugin_dest}"
echo "Verify: grok plugin validate ${plugin_dest}"
echo "Inspect: grok --plugin-dir ${plugin_dest} inspect --json"

