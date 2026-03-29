#!/usr/bin/env bash
# Install meta-skill Claude Code plugin
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing meta-skill plugin..."
claude plugin add "$SCRIPT_DIR" 2>/dev/null || {
  echo "Error: could not add meta-skill plugin. Is claude CLI available?"
  exit 1
}

echo ""
echo "Done. meta-skill replaces 6 individual plugins with /bootstrap + /run."
echo ""
echo "Usage:"
echo "  cd <your-project>"
echo "  /bootstrap          # Analyze project, generate workflow"
echo "  /run [goal]         # Execute: 逆向分析, 复刻到 SwiftUI, 代码治理, etc."
echo ""
echo "This plugin shares knowledge with Codex and OpenCode platforms."
echo "See codex/meta-skill/ and opencode/meta-skill/ for those entries."
