# Technical Design: test-backlog-fixes

## Metadata
- **Feature**: test-backlog-fixes
- **Status**: APPROVED
- **Created**: 2026-01-30

## 1. Overview

Fix all 4 root causes from the test backlog. All changes are test-only — no production code modified.

## 2. Fixes

### Fix 1: E2E harness task graph fixture mismatch (7 tests)
**Root cause**: `sample_e2e_task_graph()` returns `dict` with `{"tasks": [...]}` but `E2EHarness.setup_task_graph()` expects `list[dict]` (just the tasks list). Tests pass the full dict, iteration yields string keys.
**Fix**: Change fixture return type annotation to `dict` and update `setup_task_graph()` to accept either format — if given a dict with `"tasks"` key, extract the list. This is the minimal fix that avoids changing all callers.

### Fix 2: min_minutes parameter removed (1 test)
**Root cause**: PRF-L1-002 removed `min_minutes` from `create_task_graph_template()` but didn't update the test.
**Fix**: Remove the `min_minutes=10` kwarg from the test. Update the test to verify task estimates exist without relying on the removed parameter.

### Fix 3: claim_next_task poll timeout (2 tests)
**Root cause**: `claim_next_task()` polls with `time.sleep()` for up to 120s. With empty task list, it blocks until `max_wait`. The 60s pytest timeout fires first.
**Fix**: Patch `time.sleep` in both tests to be a no-op, and set `max_wait=0` so the function returns None immediately when no tasks exist.

### Fix 4: Real execution e2e requires Claude CLI (1 test)
**Root cause**: `harness.run()` raises `NotImplementedError("Real mode requires Claude CLI")`.
**Fix**: Add `@pytest.mark.skip(reason="Requires Claude CLI")` to the test.

## 3. Implementation Plan

### Level 1 — All 4 fixes (parallel, no dependencies)

| Task | Files | Description |
|------|-------|-------------|
| TBF-L1-001 | `tests/e2e/harness.py` | Fix setup_task_graph to handle dict-with-tasks-key |
| TBF-L1-002 | `tests/unit/test_design_cmd.py` | Remove min_minutes kwarg from test |
| TBF-L1-003 | `tests/test_worker_protocol.py`, `tests/integration/test_worker_protocol_extended.py` | Patch time.sleep + set max_wait=0 |
| TBF-L1-004 | `tests/e2e/test_real_execution.py` | Add skip marker |

### Level 2 — Verification

| Task | Files | Description |
|------|-------|-------------|
| TBF-L2-001 | None | Run full test suite with pytest-xdist |

## 4. File Ownership

| File | Task | Operation |
|------|------|-----------|
| `tests/e2e/harness.py` | TBF-L1-001 | modify |
| `tests/unit/test_design_cmd.py` | TBF-L1-002 | modify |
| `tests/test_worker_protocol.py` | TBF-L1-003 | modify |
| `tests/integration/test_worker_protocol_extended.py` | TBF-L1-003 | modify |
| `tests/e2e/test_real_execution.py` | TBF-L1-004 | modify |
