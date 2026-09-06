#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${MYSKILLS_CODEX_INSTALL_DIR:-${CODEX_HOME:-$HOME/.codex}/skills/meta-skill}"
SOURCE_REPO="${SOURCE_REPO:-https://github.com/allforai/myskills.git}"
SOURCE_REF="${SOURCE_REF:-refs/heads/main}"
SOURCE_COMMIT="${SOURCE_COMMIT:-}"

if [ -z "$SOURCE_COMMIT" ] && command -v git >/dev/null 2>&1; then
  if SOURCE_COMMIT_CANDIDATE="$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null)"; then
    SOURCE_COMMIT="$SOURCE_COMMIT_CANDIDATE"
  fi
fi

copy_dir() {
  local src="$1"
  local dst="$2"
  rm -rf "$dst"
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
}

CANONICAL_SOURCE="$SCRIPT_DIR/../../claude/meta-skill"
if [ ! -d "$CANONICAL_SOURCE/skills" ] || [ ! -d "$CANONICAL_SOURCE/knowledge" ]; then
  echo "ERROR: canonical Claude meta-skill assets are unavailable at $CANONICAL_SOURCE" >&2
  echo "Run this installer from a complete myskills source checkout." >&2
  exit 1
fi
if [ ! -f "$CANONICAL_SOURCE/skills/bootstrap/SKILL.md" ]; then
  echo "ERROR: canonical bootstrap entry is missing" >&2
  exit 1
fi

case "$INSTALL_DIR" in
  ""|/|"$HOME"|"$SCRIPT_DIR")
    echo "ERROR: refusing unsafe install target: $INSTALL_DIR" >&2
    exit 1
    ;;
esac

echo "Installing Codex meta-skill adapter to $INSTALL_DIR ..."

if [ -d "$SCRIPT_DIR/mcp-ai-gateway" ] && [ ! -d "$SCRIPT_DIR/mcp-ai-gateway/node_modules" ]; then
  echo "Building MCP AI Gateway..."
  cd "$SCRIPT_DIR/mcp-ai-gateway"
  npm install
  npm run build
fi

rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -R "$SCRIPT_DIR"/. "$INSTALL_DIR"/

# Bundle the canonical semantic source. Codex wrappers refer to this snapshot when the
# source checkout is no longer present.
mkdir -p "$INSTALL_DIR/canonical"
copy_dir "$CANONICAL_SOURCE/skills" "$INSTALL_DIR/canonical/skills"
copy_dir "$CANONICAL_SOURCE/knowledge" "$INSTALL_DIR/canonical/knowledge"

# The repository version may use relative symlinks for shared assets. Expand them so
# the installed snapshot remains usable outside the source checkout.
for rel in scripts tests mcp-ai-gateway; do
  if [ -L "$INSTALL_DIR/$rel" ]; then
    source_link="$SCRIPT_DIR/$rel"
    target="$(cd "$(dirname "$source_link")" && cd "$(readlink "$source_link")" && pwd)"
    rm -f "$INSTALL_DIR/$rel"
    copy_dir "$target" "$INSTALL_DIR/$rel"
  fi
done

# Expand compatibility links in knowledge so no installed path points back into the
# source checkout. Canonical content above remains the primary standalone source.
for installed_link in "$INSTALL_DIR"/knowledge/*; do
  if [ -L "$installed_link" ]; then
    rel="knowledge/$(basename "$installed_link")"
    source_link="$SCRIPT_DIR/$rel"
    source_parent="$(cd "$(dirname "$source_link")" && pwd)"
    target="$source_parent/$(readlink "$source_link")"
    rm -f "$installed_link"
    copy_dir "$target" "$installed_link"
  fi
done

python3 -m py_compile "$INSTALL_DIR/knowledge/flow-template.py"

{
  echo "source_repo=$SOURCE_REPO"
  echo "source_ref=$SOURCE_REF"
  echo "source_commit=$SOURCE_COMMIT"
  echo "installed_from=$SCRIPT_DIR"
} > "$INSTALL_DIR/.install-source"

echo ""
echo "Codex meta-skill adapter is ready."
echo ""
echo "Usage:"
echo "  1. Restart Codex or open a new Codex session"
echo "  2. In a target project, run: bootstrap ."
echo "  3. Bootstrap should first ask what task or goal to execute if you did not already specify it"
echo "  4. Use the generated .codex/commands/run.md entry"
echo "  5. For non-stop execution, run: python .allforai/codex/flow.py"
echo ""
echo "Notes:"
echo "  - Canonical bootstrap graph: .allforai/bootstrap/workflow.json"
echo "  - Generated Codex run entry: .codex/commands/run.md"
echo "  - Codex-only runtime helper: .allforai/codex/flow.py"
echo "  - Installed snapshot root: $INSTALL_DIR"
echo "  - Optional MCP gateway env vars: OPENROUTER_API_KEY GOOGLE_API_KEY FAL_KEY BRAVE_API_KEY"
