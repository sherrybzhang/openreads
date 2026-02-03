#!/usr/bin/env bash
set -euo pipefail

python -m sqlformat -r -k upper -i 4 schema.sql

if command -v npx >/dev/null 2>&1; then
  npx prettier --write "app/templates/**/*.html" "app/static/**/*.css"
else
  echo "prettier not found (install with: npm install)"
fi
