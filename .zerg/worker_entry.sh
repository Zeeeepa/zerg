#!/bin/bash
# ZERG Worker Entry - Invokes worker_main to execute assigned tasks
set -e

WORKER_ID=${ZERG_WORKER_ID:-0}
FEATURE=${ZERG_FEATURE}
WORKTREE=${ZERG_WORKTREE:-/workspace}
BRANCH=${ZERG_BRANCH}
SPEC_DIR=${ZERG_SPEC_DIR}

echo "========================================"
echo "ZERG Worker $WORKER_ID starting..."
echo "Feature: $FEATURE"
echo "Worktree: $WORKTREE"
echo "Branch: $BRANCH"
echo "Spec Dir: $SPEC_DIR"
echo "========================================"

cd "$WORKTREE"

# Install ZERG dependencies if not already installed
if ! python3 -c "import pydantic" 2>/dev/null; then
    echo "Installing ZERG dependencies..."
    pip3 install -q --break-system-packages -e . 2>/dev/null || \
        pip3 install -q --break-system-packages pydantic click rich jsonschema
fi

# Run the ZERG worker main
exec python3 -m zerg.worker_main \
     --worker-id "$WORKER_ID" \
     --feature "$FEATURE" \
     --worktree "$WORKTREE" \
     --branch "$BRANCH" \
     --verbose
