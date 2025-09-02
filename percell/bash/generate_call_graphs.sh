#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$REPO_ROOT/docs/graphs"

mkdir -p "$OUT_DIR"

# Build list of Python files to analyze, excluding virtualenvs, egg-info, and tests
PY_FILES=()
while IFS= read -r -d '' file; do
  PY_FILES+=("$file")
done < <(find "$REPO_ROOT/percell" -type f -name "*.py" \
  -not -path "*/venv/*" \
  -not -path "*/cellpose_venv/*" \
  -not -path "*/percell.egg-info/*" \
  -not -path "*/tests/*" -print0)

if [ "${#PY_FILES[@]}" -eq 0 ]; then
  echo "No Python files found under $REPO_ROOT/percell"
  exit 1
fi

# Prefer project venv's python to run pyan3 as a module
PYTHON_BIN="$REPO_ROOT/venv/bin/python"
if [ -x "$PYTHON_BIN" ] && "$PYTHON_BIN" -m pyan3 --help >/dev/null 2>&1; then
  PYAN3_CMD=("$PYTHON_BIN" -m pyan3)
elif command -v pyan3 >/dev/null 2>&1; then
  PYAN3_CMD=(pyan3)
else
  echo "pyan3 not found. Install with 'pip install \"pyan3<1.2\"' or activate the project's venv."
  exit 1
fi

echo "Generating Pyan3 call graphs into $OUT_DIR ..."

# Probe files individually to skip ones that crash pyan3
GOOD_FILES=()
BAD_FILES=()
for f in "${PY_FILES[@]}"; do
  if "${PYAN3_CMD[@]}" "$f" --dot --no-defines --uses --file /dev/null >/dev/null 2>&1; then
    GOOD_FILES+=("$f")
  else
    BAD_FILES+=("$f")
  fi
done

if [ ${#GOOD_FILES[@]} -eq 0 ]; then
  echo "No analyzable Python files for pyan3 (all failed probe). Aborting."
  exit 1
fi

if [ ${#BAD_FILES[@]} -gt 0 ]; then
  echo "Note: Skipping ${#BAD_FILES[@]} files that pyan3 failed to parse."
fi

# Generate a graph focused on usage (calls) edges
"${PYAN3_CMD[@]}" "${GOOD_FILES[@]}" \
  --dot \
  --colored \
  --annotated \
  --no-defines \
  --uses \
  --file "$OUT_DIR/callgraph_uses.dot"

# Also emit SVG directly to avoid Graphviz clustering issues on large graphs
"${PYAN3_CMD[@]}" "${GOOD_FILES[@]}" \
  --svg \
  --colored \
  --annotated \
  --no-defines \
  --uses \
  --file "$OUT_DIR/callgraph_uses.svg"

# Generate a graph showing definitions/structure edges
"${PYAN3_CMD[@]}" "${GOOD_FILES[@]}" \
  --dot \
  --colored \
  --annotated \
  --file "$OUT_DIR/callgraph_defines.dot"

# Also emit SVG directly
"${PYAN3_CMD[@]}" "${GOOD_FILES[@]}" \
  --svg \
  --colored \
  --annotated \
  --file "$OUT_DIR/callgraph_defines.svg"

echo "Done. Open the SVGs in $OUT_DIR"


