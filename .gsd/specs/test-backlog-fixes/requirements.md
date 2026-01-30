# Requirements: test-backlog-fixes

**Status**: APPROVED
**Created**: 2026-01-30

## Goal
Fix all 4 test failures identified in claudedocs/backlog.md (11 failing tests, 4 root causes).

## Scope

### In Scope
1. Fix e2e harness task graph parsing (7 failures) — fixture returns dict, harness expects list
2. Fix min_minutes regression (1 failure) — test uses removed parameter
3. Fix claim_next_task poll timeout (2 failures) — mock time.sleep to avoid 60s timeout
4. Skip real execution e2e test (1 failure) — requires Claude CLI not available in test env

### Out of Scope
- Changing claim_next_task production behavior
- Modifying worker_protocol.py production code
