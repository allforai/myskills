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
echo "Done. meta-skill v0.6.0 installed (26 capabilities, 5 domain knowledge files)."
echo ""
echo "Usage:"
echo "  cd <your-project>"
echo "  /setup              # Configure external capabilities (optional)"
echo "  /bootstrap          # Analyze project, generate workflow"
echo "  /run [goal]         # Execute toward a goal"
echo ""
echo "Examples:"
echo "  /run 逆向分析       # Reverse-engineer existing project"
echo "  /run 从零构建       # Build new product from concept"
echo "  /run 代码治理       # Code quality optimization"
