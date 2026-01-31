# /zerg:git

Git operations with intelligent commit messages and a structured finish workflow.

## Synopsis

```
/zerg:git --action commit|branch|merge|sync|history|finish
          [--push]
          [--base main]
```

## Description

The `git` command wraps common Git operations with ZERG-aware intelligence. It auto-generates conventional commit messages from staged changes, manages branches, performs merges with conflict detection, and provides a structured finish workflow for completing development branches.

### Actions

**commit** -- Stage and commit changes with an auto-generated conventional commit message. Optionally push to the remote.

```
/zerg:git --action commit [--push]
```

**branch** -- Create and switch to a new branch.

```
/zerg:git --action branch --name feature/auth
```

**merge** -- Merge a branch with intelligent conflict detection.

```
/zerg:git --action merge --branch feature/auth --strategy squash
```

**sync** -- Synchronize the local branch with its remote tracking branch.

```
/zerg:git --action sync
```

**history** -- Analyze commit history and generate a changelog from a given starting point.

```
/zerg:git --action history --since v1.0.0
```

**finish** -- Complete a development branch with a structured set of options. This action presents an interactive menu:

```
Implementation complete. All tests passing. What would you like to do?

1. Merge back to main locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

### Conventional Commit Types

Auto-generated commit messages follow the conventional commits specification:

| Type | Description |
|------|-------------|
| `feat` | New features |
| `fix` | Bug fixes |
| `docs` | Documentation changes |
| `style` | Formatting (no logic changes) |
| `refactor` | Code restructuring |
| `test` | Test additions or modifications |
| `chore` | Maintenance tasks |

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--action` | (required) | Git operation to perform. Accepts `commit`, `branch`, `merge`, `sync`, `history`, or `finish`. |
| `--push` | off | Push to remote after committing or merging. |
| `--base` | `main` | Base branch for the finish workflow. |
| `--name` | -- | Branch name for the `branch` action. |
| `--branch` | -- | Source branch for the `merge` action. |
| `--strategy` | -- | Merge strategy (e.g., `squash`) for the `merge` action. |
| `--since` | -- | Starting tag or commit for the `history` action. |

## Examples

Commit staged changes with an auto-generated message:

```
/zerg:git --action commit
```

Commit and push in one step:

```
/zerg:git --action commit --push
```

Create a new feature branch:

```
/zerg:git --action branch --name feature/auth
```

Complete the current branch with the finish workflow:

```
/zerg:git --action finish --base main
```

Generate a changelog since v1.0.0:

```
/zerg:git --action history --since v1.0.0
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Operation successful |
| 1 | Operation failed |
| 2 | Tests must pass (required for `finish`) |

## Task Tracking

This command creates a Claude Code Task with the subject prefix `[Git]` on invocation, updates it to `in_progress` immediately, and marks it `completed` on success.

## See Also

- [[Command-review]] -- Review code before committing or finishing
- [[Command-build]] -- Verify the build passes before finishing a branch
- [[Command-test]] -- Ensure tests pass before the finish workflow
