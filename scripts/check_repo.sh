#!/usr/bin/env bash
set -euo pipefail

required_files=(
  "README.md"
  "CONTRIBUTING.md"
  "AGENTS.md"
  "docs/PROJECT_BRIEF.md"
  "docs/ROADMAP.md"
  "docs/ARCHITECTURE.md"
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

if git ls-files | grep -E '(^|/)\.env($|\.local$|\.production$|\.development$|\.test$)' >/dev/null; then
  echo "tracked environment secret file detected"
  exit 1
fi

echo "repo check passed"
