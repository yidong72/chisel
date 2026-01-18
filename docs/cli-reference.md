# CLI Reference

Complete documentation for all Chisel commands.

## Global Options

These options work with any command:

| Option | Description |
|--------|-------------|
| `--project PATH` | Override project path (default: auto-discover) |
| `--json` | Output in JSON format |
| `--help` | Show help message |

## Commands

### chisel init

Initialize a new Chisel project.

```bash
chisel init [--json]
```

Creates `.chisel/` directory in current folder with:
- `chisel.db`: SQLite database
- Default configuration

**Example:**
```bash
$ chisel init --json
{
  "message": "Initialized chisel project in /home/user/my-project",
  "project_root": "/home/user/my-project",
  "database": "/home/user/my-project/.chisel/chisel.db"
}
```

---

### chisel info

Show current project information.

```bash
chisel info [--json]
```

**Example:**
```bash
$ chisel info --json
{
  "project_root": "/home/user/my-project",
  "database": "/home/user/my-project/.chisel/chisel.db",
  "config": {
    "project_name": "my-project",
    "id_prefix": "ch",
    "default_priority": "2"
  }
}
```

---

### chisel create

Create a new task.

```bash
chisel create TITLE [OPTIONS] [--json]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-t, --type` | string | task | Task type |
| `-p, --priority` | int | 2 | Priority (0-4) |
| `-d, --description` | string | | Description |
| `--parent` | string | | Parent task ID |
| `--points` | int | | Story points |
| `--estimate` | int | | Time estimate (minutes) |
| `--assignee` | string | | Assignee |
| `--labels` | string | | Comma-separated labels |
| `--criteria` | string | | Acceptance criteria (repeatable) |

**Task Types:** task, epic, bug, spike, chore

**Priority Levels:**
- 0: Critical
- 1: High
- 2: Medium (default)
- 3: Low
- 4: Backlog

**Example:**
```bash
$ chisel create "Fix login bug" -t bug -p 1 -d "Users can't login with email" --json
{
  "task": {
    "id": "ch-abc123",
    "title": "Fix login bug",
    "task_type": "bug",
    "priority": 1,
    "status": "open",
    ...
  },
  "message": "Created task ch-abc123"
}
```

---

### chisel list

List tasks with optional filters.

```bash
chisel list [OPTIONS] [--json]
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--status` | string | Filter by status |
| `--priority` | int | Filter by priority |
| `--type` | string | Filter by task type |
| `--parent` | string | Filter by parent ID |
| `--assignee` | string | Filter by assignee |
| `--labels` | string | Filter by labels |
| `--limit` | int | Maximum results |

**Example:**
```bash
$ chisel list --status open --priority 1 --limit 5 --json
{
  "tasks": [
    {"id": "ch-abc123", "title": "Fix login bug", "priority": 1, ...},
    {"id": "ch-def456", "title": "Add OAuth", "priority": 1, ...}
  ]
}
```

---

### chisel show

Show detailed task information.

```bash
chisel show TASK_ID [--json]
```

**Example:**
```bash
$ chisel show ch-abc123 --json
{
  "task": {...},
  "dependencies": [...],
  "dependents": [...],
  "children": [...]
}
```

---

### chisel update

Update a task.

```bash
chisel update TASK_ID [OPTIONS] [--json]
```

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--title` | string | New title |
| `-d, --description` | string | New description |
| `--type` | string | New task type |
| `-p, --priority` | int | New priority |
| `-s, --status` | string | New status |
| `--points` | int | Story points |
| `--estimate` | int | Time estimate (minutes) |
| `--assignee` | string | Assignee |
| `--labels` | string | Labels (replaces existing) |

**Statuses:** open, in_progress, blocked, review, done, cancelled

**Example:**
```bash
$ chisel update ch-abc123 --status in_progress --json
{
  "task": {"id": "ch-abc123", "status": "in_progress", ...},
  "message": "Updated task ch-abc123"
}
```

---

### chisel close

Close a task (mark as done).

```bash
chisel close TASK_ID [--reason TEXT] [--json]
```

Runs pre-close hooks before closing. Fails if any hook fails.

**Example:**
```bash
$ chisel close ch-abc123 --reason "Fixed the login issue" --json
{
  "task": {"id": "ch-abc123", "status": "done", ...},
  "message": "Closed task ch-abc123",
  "hook_results": [...]
}
```

---

### chisel reopen

Reopen a closed or cancelled task.

```bash
chisel reopen TASK_ID [--json]
```

---

### chisel ready

Show tasks ready to work on.

```bash
chisel ready [--limit N] [--json]
```

Returns open tasks with no blocking dependencies, ordered by priority.

**Example:**
```bash
$ chisel ready --limit 3 --json
{
  "tasks": [
    {"id": "ch-abc123", "title": "High priority task", "priority": 1, ...},
    {"id": "ch-def456", "title": "Medium task", "priority": 2, ...}
  ]
}
```

---

### chisel blocked

Show blocked tasks.

```bash
chisel blocked [--json]
```

Returns tasks with unresolved blocking dependencies.

---

### chisel decompose

Break down a task into subtasks.

```bash
chisel decompose TASK_ID SUBTASK1 SUBTASK2 ... [--points N,N,...] [--json]
```

**Example:**
```bash
$ chisel decompose ch-epic123 "Design" "Implement" "Test" --points 2,5,3 --json
{
  "parent": {"id": "ch-epic123", "task_type": "epic", ...},
  "subtasks": [
    {"id": "ch-sub1", "title": "Design", "story_points": 2, ...},
    {"id": "ch-sub2", "title": "Implement", "story_points": 5, ...},
    {"id": "ch-sub3", "title": "Test", "story_points": 3, ...}
  ],
  "message": "Created 3 subtasks under ch-epic123"
}
```

---

### chisel tree

Show task hierarchy.

```bash
chisel tree TASK_ID [--json]
```

**Example:**
```bash
$ chisel tree ch-epic123 --json
{
  "tree": {
    "task": {"id": "ch-epic123", "title": "Epic", ...},
    "children": [
      {"task": {"id": "ch-sub1", ...}, "children": []},
      {"task": {"id": "ch-sub2", ...}, "children": []}
    ]
  }
}
```

---

### chisel dep add

Add a dependency.

```bash
chisel dep add TASK_ID --blocked-by BLOCKER_ID [--type TYPE] [--json]
```

**Example:**
```bash
$ chisel dep add ch-taskB --blocked-by ch-taskA --json
{
  "dependency": {
    "task_id": "ch-taskB",
    "depends_on_id": "ch-taskA",
    "dep_type": "blocks"
  },
  "message": "Added dependency: ch-taskB blocked by ch-taskA"
}
```

---

### chisel dep remove

Remove a dependency.

```bash
chisel dep remove TASK_ID BLOCKER_ID [--json]
```

---

### chisel dep list

List dependencies for a task.

```bash
chisel dep list TASK_ID [--json]
```

**Example:**
```bash
$ chisel dep list ch-taskB --json
{
  "task_id": "ch-taskB",
  "blocked_by": [
    {"task_id": "ch-taskB", "depends_on_id": "ch-taskA", "dep_type": "blocks"}
  ],
  "blocks": []
}
```

---

### chisel hook set

Add a quality hook.

```bash
chisel hook set EVENT COMMAND [--json]
```

**Events:** pre-close, post-create

**Example:**
```bash
$ chisel hook set pre-close "pytest tests/ -q" --json
{
  "hook": {"id": 1, "event": "pre-close", "command": "pytest tests/ -q", "enabled": true},
  "message": "Added hook for pre-close: pytest tests/ -q"
}
```

---

### chisel hook list

List configured hooks.

```bash
chisel hook list [--event EVENT] [--json]
```

---

### chisel hook remove

Remove a hook.

```bash
chisel hook remove HOOK_ID [--json]
```

---

### chisel validate

Run validation hooks for a task.

```bash
chisel validate TASK_ID [--json]
```

**Example:**
```bash
$ chisel validate ch-abc123 --json
{
  "task_id": "ch-abc123",
  "valid": true,
  "hook_results": [
    {"command": "pytest tests/ -q", "success": true, "return_code": 0, ...}
  ]
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (not found, validation failed, etc.) |
