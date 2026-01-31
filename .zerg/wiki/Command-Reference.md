# ZERG Command Reference

This page provides an index of all ZERG commands. Each command has its own detailed reference page.

## Workflow Overview

ZERG commands follow a sequential workflow. The typical order of operations is:

```
init --> plan --> design --> rush --> status/logs --> merge --> cleanup
```

During execution, use `stop` to halt workers, `retry` to re-run failed tasks, and `logs` to inspect worker output.

## Command Index

| Command | Purpose | Phase |
|---------|---------|-------|
| [[Command-init]] | Initialize ZERG for a new or existing project | Setup |
| [[Command-plan]] | Capture requirements for a feature | Planning |
| [[Command-design]] | Generate architecture and task graph for parallel execution | Design |
| [[Command-rush]] | Launch parallel workers to execute the task graph | Execution |
| [[Command-status]] | Display current execution status and progress | Monitoring |
| [[Command-logs]] | Stream, filter, and aggregate worker logs | Monitoring |
| [[Command-stop]] | Stop workers gracefully or forcefully | Control |
| [[Command-retry]] | Retry failed or blocked tasks | Recovery |
| [[Command-merge]] | Trigger or manage level merge operations | Integration |
| [[Command-cleanup]] | Remove ZERG artifacts and clean up resources | Teardown |

## Command Categories

### Setup

- **[[Command-init]]** -- Run once per project to detect languages, generate configuration, and create the `.zerg/` directory structure.

### Planning and Design

- **[[Command-plan]]** -- Interactive requirements gathering. Produces `requirements.md` in the spec directory.
- **[[Command-design]]** -- Generates `design.md` and `task-graph.json`. Breaks work into parallelizable tasks with exclusive file ownership.

### Execution

- **[[Command-rush]]** -- Launches worker containers or processes. Assigns tasks by level and monitors execution.
- **[[Command-stop]]** -- Graceful or forced shutdown of running workers.
- **[[Command-retry]]** -- Re-queues failed tasks for execution.

### Monitoring

- **[[Command-status]]** -- Snapshot of progress across all levels, workers, and tasks.
- **[[Command-logs]]** -- Access structured JSONL logs, filter by worker, task, level, phase, or event type.

### Integration and Teardown

- **[[Command-merge]]** -- Merges worker branches after each level, runs quality gates (lint, test, typecheck).
- **[[Command-cleanup]]** -- Removes worktrees, branches, containers, and state files. Preserves spec files and merged code.

## Global Concepts

### Feature Name

Most commands auto-detect the active feature from `.gsd/.current-feature`. You can override this with `--feature <name>` where supported.

### Task System

All commands integrate with Claude Code's Task system for coordination and state tracking. The Task system is the authoritative source of truth; state JSON files in `.zerg/state/` are supplementary.

### Levels

Tasks are grouped into dependency levels. All tasks in Level N must complete before any Level N+1 task begins. Within a level, tasks run in parallel.

### File Ownership

Each task exclusively owns specific files. No two tasks modify the same file, which eliminates merge conflicts during parallel execution.
