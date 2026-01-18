# Agent Instructions for Chisel

Task management CLI. All commands support `--json` for machine-readable output.

## Quick Start

```bash
chisel ready --json           # Find next task to work on
chisel update ID -s in_progress --json  # Start working
chisel close ID --reason "Done" --json  # Complete task
```

## Core Commands

| Command | Purpose |
|---------|---------|
| `chisel init` | Initialize project (creates `.chisel/`) |
| `chisel ready` | Get unblocked tasks by priority |
| `chisel create "Title" -p 1 -t bug` | Create task |
| `chisel show ID` | View task details |
| `chisel update ID -s STATUS` | Update task |
| `chisel close ID --reason "..."` | Complete task |
| `chisel list --status open` | List tasks with filters |
| `chisel decompose ID "Sub1" "Sub2"` | Break down task |
| `chisel tree ID` | View hierarchy |
| `chisel dep add B --blocked-by A` | Add dependency |
| `chisel blocked` | Show blocked tasks |
| `chisel validate ID` | Run quality hooks |

## Workflow

1. **Find work**: `chisel ready --json`
2. **Start task**: `chisel update ID -s in_progress --json`
3. **Complete**: `chisel close ID --reason "Description" --json`

For large tasks (>8 points), decompose first:
```bash
chisel decompose ID "Design" "Implement" "Test" --points 2,5,3 --json
```

## Priority Levels

| Priority | Meaning |
|----------|---------|
| 0 | Critical - drop everything |
| 1 | High - do today |
| 2 | Medium - this week (default) |
| 3 | Low - when time permits |
| 4 | Backlog - someday |

## Task Types

`task` (default), `epic`, `bug`, `spike`, `chore`

## Statuses

`open` → `in_progress` → `done`

Also: `blocked`, `review`, `cancelled`

## JSON Response Format

```json
{"task": {...}, "message": "..."}   // Success
{"tasks": [...]}                     // List
{"error": "..."}                     // Error
```

## Key Rules

- Always use `--json` for programmatic parsing
- Check `chisel ready` before starting work
- Update status when starting/finishing tasks
- Decompose epics into subtasks
