# ZERG Development Backlog

**Updated**: 2026-01-31

## Completed

| # | Item | Completed | Commit |
|---|------|-----------|--------|
| 1 | State file IPC: Workers write WorkerState, orchestrator reloads in poll loop | 2026-01-28 | a189fc7 |
| 2 | Container execution: Docker image, ContainerLauncher, resource limits, health checks, security hardening | 2026-01-28 | ce7d58e |
| 4 | Debug cleanup: Gate verbose diagnostic details behind `--verbose` in troubleshoot.py | 2026-01-28 | 763ef8c |
| 3 | Test coverage: 96.53% coverage across 64 modules (4468 tests), P0 files all at 100% | 2026-01-28 | 06abc7c + 1dc4f8e |
| 6 | Log aggregation: Structured JSONL logging per worker, per-task artifact capture, read-side aggregation, CLI query/filter | 2026-01-29 | a0b6e66 |
| 5 | Production dogfooding: Real Docker E2E tests against ContainerManager and ContainerLauncher | 2026-01-29 | — |
| 7 | Task retry logic: Auto-retry failed tasks with backoff, max attempts | 2026-01-29 | — |
| 8 | Dry-run improvements: Pre-flight checks, risk scoring, what-if analysis, Gantt timeline, projected snapshots | 2026-01-29 | — |
| 9 | Troubleshoot enhancement: World-class debugger — multi-language error intel (Python/JS/Go/Rust/Java/C++), Bayesian hypothesis engine (33 patterns), cross-worker log correlation, code-aware recovery, environment diagnostics. 7 new modules, 383 tests. | 2026-01-30 | 53a0a97..4d1e407 |
| 10 | `/z` shortcut alias: `install_commands.py` generates `z:` symlinks for all `zerg:` commands. Both prefixes work with full parity. | 2026-01-30 | — |
| 11 | Rename troubleshoot → debug: Cascaded rename across all code, commands (.zerg/ scripts, slash commands, CLI), tests, and documentation project-wide. | 2026-01-30 | — |
| 12 | Performance analysis `zerg analyze --performance`: 140-factor audit across 16 categories, 11 optional tool adapters (semgrep, radon, lizard, vulture, jscpd, deptry, pipdeptree, dive, hadolint, trivy, cloc), stack detection, graceful degradation, 4 output formats (Rich/JSON/SARIF/Markdown). New `zerg/performance/` submodule (20 files), 95 tests. | 2026-01-30 | 6549ca3..b7d4811 |

## Backlog

| # | Area | Description | Effort | Status |
|---|------|-------------|--------|--------|
