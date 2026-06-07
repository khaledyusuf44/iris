#!/usr/bin/env bash
set -euo pipefail

required_files=(
  ".env.example"
  "README.md"
  "CONTRIBUTING.md"
  "AGENTS.md"
  "app.py"
  "docs/PROJECT_BRIEF.md"
  "docs/ROADMAP.md"
  "docs/ARCHITECTURE.md"
  "requirements.txt"
  "iris/__init__.py"
  "iris/engine.py"
  "iris/cli.py"
  "iris/ui.py"
  "iris/gate.py"
  "iris/seeds.py"
  "iris/spiral.py"
  "tests/test_engine.py"
  "scripts/validate_gate.py"
)

missing=0

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "missing required file: $file"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

if git ls-files | grep -E '(^|/)\.env($|[^/])' | grep -v -E '(^|/)\.env\.example$' >/dev/null; then
  echo "tracked environment secret file detected"
  exit 1
fi

if git ls-files | grep -E '(^|/)0[1-9]-.+\.md$' >/dev/null; then
  echo "tracked local handoff/task markdown detected"
  exit 1
fi

echo "repo check passed"
