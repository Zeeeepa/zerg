# ZERG

**Parallel Claude Code execution system.** ZERG coordinates multiple Claude Code instances to work on features simultaneously, splitting tasks by file ownership to eliminate merge conflicts. Think of it as a swarm of AI workers building your project in parallel.

## Key Features

- **Parallel execution** -- multiple Claude Code instances working concurrently on isolated file sets
- **Dependency-aware scheduling** -- tasks grouped into levels; each level completes before the next begins
- **Exclusive file ownership** -- no merge conflicts by design
- **Spec-driven workers** -- zerglings read spec files, not conversation history, making them stateless and restartable
- **Automated verification** -- every task has a verification command with a pass/fail gate
- **Cross-cutting capabilities** -- analysis depth tiers, token efficiency, MCP routing, TDD enforcement, and more

## Quick Start

### Install

```bash
pip install zerg-ai
```

### Basic Workflow

```bash
# 1. Plan a feature
/zerg:plan user-auth

# 2. Design architecture and task graph
/zerg:design

# 3. Launch parallel workers
/zerg:rush --workers=5

# 4. Monitor progress
/zerg:status
```

ZERG captures requirements, creates an architecture with atomic tasks, then launches workers that execute in parallel -- merging and running quality gates after each dependency level.

## What's Next

- [**Tutorial**](tutorial-minerals-store.md) -- Build a complete store with ZERG from scratch
- [**Quick Reference**](commands-quick.md) -- Fast lookup for all commands and flags
- [**Command Guide**](commands-deep.md) -- Detailed explanations of every command
- [**Configuration**](configuration.md) -- Customize timeouts, quality gates, MCP servers, and more
