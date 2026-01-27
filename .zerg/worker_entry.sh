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

# Fix git worktree paths for container environment
# Git worktrees have several files with absolute paths that need to be fixed:
# 1. .git file in worktree -> points to worktree metadata
# 2. gitdir in worktree metadata -> points back to worktree's .git
# 3. commondir in worktree metadata -> points to main repo's .git
if [ -n "$ZERG_GIT_WORKTREE_DIR" ] && [ -d "$ZERG_GIT_WORKTREE_DIR" ]; then
    echo "Fixing git worktree paths..."
    echo "  Worktree metadata: $ZERG_GIT_WORKTREE_DIR"
    echo "  Main git dir: $ZERG_GIT_MAIN_DIR"

    # 1. Fix worktree's .git file to point to mounted worktree metadata
    echo "gitdir: $ZERG_GIT_WORKTREE_DIR" > "$WORKTREE/.git"

    # 2. Fix gitdir to point back to worktree's .git
    if [ -f "$ZERG_GIT_WORKTREE_DIR/gitdir" ]; then
        echo "$WORKTREE/.git" > "$ZERG_GIT_WORKTREE_DIR/gitdir"
    fi

    # 3. Fix commondir to point to mounted main repo's .git
    if [ -n "$ZERG_GIT_MAIN_DIR" ] && [ -f "$ZERG_GIT_WORKTREE_DIR/commondir" ]; then
        echo "$ZERG_GIT_MAIN_DIR" > "$ZERG_GIT_WORKTREE_DIR/commondir"
    fi

    echo "Git worktree paths fixed"
fi

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
