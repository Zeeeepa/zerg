# Dynamic Devcontainer - Task Backlog

**Feature**: Dynamic devcontainer configuration + automated container worker execution
**Status**: ✅ Nearly Complete (10/12)
**Created**: 2026-01-25
**Updated**: 2026-01-26
**Total Tasks**: 12 | **Levels**: 5 | **Max Parallelization**: 4

---

## Execution Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 12 |
| Completed | 10 |
| Remaining | 2 |
| Critical Path Tasks | 5 (DC-002 → DC-003 → DC-004 → DC-009 → DC-012) |

---

## Level 1: Foundation (Parallel: 3 tasks) ✅ Complete

| ID | Task | Files Owned | Status | Verification |
|----|------|-------------|--------|--------------|
| **DC-001** | Update init.py to use ProjectStack | `zerg/commands/init.py` | ✅ Complete | `zerg init --detect` shows multiple langs |
| **DC-002** ⭐ | Create devcontainer_features.py | `zerg/devcontainer_features.py` | ✅ Complete | Import succeeds |
| **DC-006** | Implement ContainerLauncher base | `zerg/launcher.py` | ✅ Complete | Class inherits WorkerLauncher |

---

## Level 2: Core Generators (Parallel: 2 tasks) ✅ Complete

| ID | Task | Files Owned | Deps | Status | Verification |
|----|------|-------------|------|--------|--------------|
| **DC-003** ⭐ | Create DynamicDevcontainerGenerator | `zerg/devcontainer_features.py` | DC-002 | ✅ Complete | Generates multi-lang config |
| **DC-007** | Add container spawn + claude exec | `zerg/launcher.py`, `.zerg/worker_entry.sh` | DC-006 | ✅ Complete | worker_entry.sh exists |

---

## Level 3: Integration (Parallel: 3 tasks) ✅ Complete

| ID | Task | Files Owned | Deps | Status | Verification |
|----|------|-------------|------|--------|--------------|
| **DC-004** ⭐ | Update create_devcontainer() | `zerg/commands/init.py` | DC-001, DC-003 | ✅ Complete | Multi-lang devcontainer.json |
| **DC-005** | Update .zerg/devcontainer.py | `.zerg/devcontainer.py` | DC-003 | ✅ Complete | Multi-lang support |
| **DC-008** | Add auto-detect launcher mode | `zerg/orchestrator.py` | DC-006 | ✅ Complete | Auto-detects container mode |

---

## Level 4: Orchestration (Sequential: 2 tasks) ✅ Complete

| ID | Task | Files Owned | Deps | Status | Verification |
|----|------|-------------|------|--------|--------------|
| **DC-009** ⭐ | Wire ContainerLauncher to orchestrator | `zerg/orchestrator.py` | DC-007, DC-008 | ✅ Complete | Orchestrator uses containers |
| **DC-010** | Add --mode flag to rush | `zerg/commands/rush.py` | DC-009 | ✅ Complete | CLI shows --mode option |

---

## Level 5: Polish (Parallel: 2 tasks) 🟡 In Progress

| ID | Task | Files Owned | Deps | Status | Verification |
|----|------|-------------|------|--------|--------------|
| **DC-011** | Update skill file docs | `.claude/commands/zerg:*.md` | DC-010 | ✅ Complete | Docs mention container mode |
| **DC-012** ⭐ | Integration test | `tests/integration/test_container_flow.py` | All | ⬜ Pending | Tests pass |

---

## Critical Path ⭐

```
DC-002 (15m) → DC-003 (30m) → DC-004 (25m) → DC-009 (35m) → DC-012 (30m)
                                                              ↑ only remaining
```

---

## File Ownership Matrix

| File | Owner Task | Action | Status |
|------|-----------|--------|--------|
| `zerg/commands/init.py` | DC-001, DC-004 | Modify | ✅ |
| `zerg/devcontainer_features.py` | DC-002, DC-003 | Create, Modify | ✅ |
| `zerg/launcher.py` | DC-006, DC-007 | Modify | ✅ |
| `zerg/orchestrator.py` | DC-008, DC-009 | Modify | ✅ |
| `zerg/commands/rush.py` | DC-010 | Modify | ✅ |
| `.zerg/devcontainer.py` | DC-005 | Modify | ✅ |
| `.zerg/worker_entry.sh` | DC-007 | Create | ✅ |
| `.claude/commands/zerg:init.md` | DC-011 | Modify | ✅ |
| `.claude/commands/zerg:rush.md` | DC-011 | Modify | ✅ |
| `tests/integration/test_container_flow.py` | DC-012 | Create | ⬜ |

---

## Progress Tracker

```
Last Updated: 2026-01-26

Level 1: ✅✅✅ (3/3)
Level 2: ✅✅ (2/2)
Level 3: ✅✅✅ (3/3)
Level 4: ✅✅ (2/2)
Level 5: ✅⬜ (1/2)

Overall: 10/12 (83%)
```

---

## Remaining Work

Only DC-012 (Integration test for container flow) remains:

```bash
# Verification command:
pytest tests/integration/test_container_flow.py -v
```

The test should verify:
1. Container spawning works
2. Worker entry script executes correctly
3. Claude Code runs inside container
4. File isolation is maintained
5. Results are collected properly

---

## Notes

- Container mode is functional and tested manually
- Integration test deferred for future session
- All skill docs updated to document container mode
