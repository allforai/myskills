#!/usr/bin/env bash
# Rebuild the Ledgerly discovery fixture as a git repo with its three commits.
# Usage: build.sh <target-dir>   (target must not exist; never point it inside this repo)
set -euo pipefail
src="$(cd "$(dirname "$0")/src" && pwd)"
dst="${1:?target dir}"
[ -e "$dst" ] && { echo "refusing: $dst exists" >&2; exit 1; }
mkdir -p "$dst"
cp -R "$src"/. "$dst"/
cd "$dst"
git init -q && git config user.email dev@example.com && git config user.name dev
git add README.md requirements.txt app.py pdf.py templates static
git commit -qm "Ledgerly: clients, invoices, send, paid, pdf" --date="2026-08-01T10:00:00"
git add weather.py
git commit -qm "Add weather widget on dashboard for demo day (sales asked for something live on the first screen)" --date="2026-08-20T10:00:00"
git add docs
git commit -qm "docs: cross-exam completion report" --date="2026-09-16T10:00:00"
git log --oneline
