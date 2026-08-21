#!/usr/bin/env bash
# Run the content tests. See tests/README.md.
#
#   tests/run.sh            fast suite (~10 s) — everything except diagrams
#   tests/run.sh diagrams   render every mermaid diagram (~8 min)
#   tests/run.sh all        both
#
# Creates .venv on first run.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if [ ! -x .venv/bin/python ]; then
  echo "creating .venv"
  python3 -m venv .venv
  .venv/bin/pip install --quiet -r tests/requirements.txt
fi
PYTHON=.venv/bin/python

mode="${1:-fast}"

case "$mode" in
  fast)
    "$PYTHON" -m pytest \
      --deselect tests/test_links_and_diagrams.py::test_mermaid_diagram_parses
    ;;
  diagrams)
    command -v mmdc >/dev/null 2>&1 || {
      echo "mermaid-cli missing: npm install -g @mermaid-js/mermaid-cli" >&2
      exit 1
    }
    "$PYTHON" -m pytest tests/test_links_and_diagrams.py -k mermaid
    ;;
  all)
    "$0" fast && "$0" diagrams
    ;;
  *)
    echo "usage: tests/run.sh [fast|diagrams|all]" >&2
    exit 2
    ;;
esac
