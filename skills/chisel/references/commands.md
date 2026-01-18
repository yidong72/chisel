# Chisel CLI Reference

## Global Options

| Option | Description |
|--------|-------------|
| `--project PATH` | Override project path (auto-discovers by default) |
| `--json` | **Always use this** - JSON output for parsing |

## Project Commands

| Command | Description |
|---------|-------------|
| `chisel init` | Initialize project in current directory |
| `chisel info` | Show project info and configuration |

## Task Commands

### chisel create

Create a new task.

```bash
chisel create "Title" [options] --json
```

| Option | Description |
|--------|-------------|
| `-t, --type TYPE` | task, epic, bug, spike, chore |
| `-p, --priority N` | 0=critical, 1=high, 2=medium, 3=low, 4=backlog |
| `-d, --description TEXT` | Detailed description |
| `--parent ID` | Parent task ID (for subtasks) |
| `--points N` | Story points estimate |
| `--estimate N` | Time estimate in minutes |
| `--assignee TEXT` | Assignee name |
| `--labels TEXT` | Comma-separated labels |
| `--criteria TEXT` | Acceptance criteria (repeatable) |

### chisel list

List tasks with filters.

```bash
chisel list [options] --json
```

| Option | Description |
|--------|-------------|
| `--status STATUS` | Filter: open, in_progress, blocked, review, done, cancelled |
| `--priority N` | Filter by priority (0-4) |
| `--type TYPE` | Filter by type |
| `--parent ID` | Filter by parent task |
| `--assignee TEXT` | Filter by assignee |
| `--labels TEXT` | Filter by labels |
| `--limit N` | Max results |

### chisel show

Show task details with dependencies and children.

```bash
chisel show ID --json
```

### chisel update

Update task properties.

```bash
chisel update ID [options] --json
```

| Option | Description |
|--------|-------------|
| `--title TEXT` | New title |
| `-d, --description TEXT` | New description |
| `--type TYPE` | New type |
| `-p, --priority N` | New priority |
| `-s, --status STATUS` | New status |
| `--points N` | Story points |
| `--assignee TEXT` | Assignee |
| `--labels TEXT` | Labels (replaces existing) |

### chisel close

Complete a task.

```bash
chisel close ID --reason "What was done" --json
```

Runs pre-close hooks before closing. Fails if hooks fail.

### chisel reopen

Reopen a closed/cancelled task.

```bash
chisel reopen ID --json
```

### chisel ready

**Most important command** - Get tasks ready to work on.

```bash
chisel ready [--limit N] --json
```

Returns open tasks with no blockers, sorted by priority.

### chisel blocked

Show tasks that are blocked by other tasks.

```bash
chisel blocked --json
```

## Decomposition Commands

### chisel decompose

Break a task into subtasks.

```bash
chisel decompose ID "Sub1" "Sub2" "Sub3" [--points 2,3,2] --json
```

Automatically converts parent to epic type.

### chisel tree

Show task hierarchy.

```bash
chisel tree ID --json
```

## Dependency Commands

### chisel dep add

Add blocking dependency (B waits for A).

```bash
chisel dep add B --blocked-by A --json
```

### chisel dep remove

Remove a dependency.

```bash
chisel dep remove TASK_ID BLOCKER_ID --json
```

### chisel dep list

List dependencies for a task.

```bash
chisel dep list ID --json
```

## Hook Commands

### chisel hook set

Add a quality hook (runs before close).

```bash
chisel hook set pre-close "pytest tests/ -q" --json
chisel hook set pre-close "ruff check ." --json
```

### chisel hook list

List configured hooks.

```bash
chisel hook list --json
```

### chisel hook remove

Remove a hook.

```bash
chisel hook remove HOOK_ID --json
```

### chisel validate

Run pre-close hooks manually.

```bash
chisel validate ID --json
```

## Response Examples

### Task Created
```json
{
  "task": {"id": "ch-abc123", "title": "...", "status": "open", ...},
  "message": "Created task ch-abc123"
}
```

### Task List
```json
{
  "tasks": [
    {"id": "ch-abc", "title": "...", "priority": 1, ...},
    {"id": "ch-def", "title": "...", "priority": 2, ...}
  ]
}
```

### Dependency Added
```json
{
  "dependency": {"task_id": "ch-b", "depends_on_id": "ch-a", "dep_type": "blocks"},
  "message": "Added dependency: ch-b blocked by ch-a"
}
```

### Error
```json
{
  "error": "Task not found"
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (not found, validation failed, hook failed) |
