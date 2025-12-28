#!/usr/bin/env bash
# radonhal - small wrapper to run the project's main.py analyzer
# Usage: ./radonhal.sh ./frontend/src ./backend

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <root_dir1> [<root_dir2> ...]"
  echo "Example: $0 ./frontend/src ./backend"
  exit 2
fi

echo "Directories to analyze: $@"
read -r -p "Press Enter to run analysis (or Ctrl-C to cancel)..."

# Run main.py with the provided directories
python3 "$(dirname "$0")/main.py" "$@"
