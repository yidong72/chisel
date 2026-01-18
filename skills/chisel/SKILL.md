---
name: chisel
description: Task management CLI for tracking work, breaking down features, and managing dependencies. Use when the user asks about tasks, what to work on, or needs help organizing work.

<example>
user: "What should I work on next?"
assistant: "Let me check for ready tasks."
[Runs: chisel ready --json]
[Parses JSON response to find highest priority unblocked task]
"The highest priority task is ch-abc123: 'Fix login bug' (P1). Should I start working on it?"
</example>

<example>
user: "I need to implement user authentication"
assistant: "I'll create an epic and break it down into manageable subtasks."
[Runs: chisel create "User Authentication" -t epic -p 1 --json]
[Runs: chisel decompose ch-xxx "Design auth flow" "Implement OAuth" "Create login UI" "Add session management" "Write tests" --points 2,5,5,3,3 --json]
"Created epic ch-xxx with 5 subtasks. The first task 'Design auth flow' is ready to start."
</example>

<example>
user: "I finished the login feature"
assistant: "I'll close that task and find the next one."
[Runs: chisel close ch-abc123 --reason "Implemented login with OAuth support" --json]
[Runs: chisel ready --json]
"Closed ch-abc123. Next up is ch-def456: 'Add password reset' (P2)."
</example>

<example>
user: "This task is blocked by the API work"
assistant: "I'll add that dependency."
[Runs: chisel dep add ch-current --blocked-by ch-api-task --json]
"Added dependency. ch-current is now blocked by ch-api-task and won't appear in ready tasks until that's done."
</example>
---

# Chisel - Task Management Skill

Chisel is a CLI tool for managing tasks. **Always use `--json` flag** for machine-readable output.

## When to Use This Skill

- User asks "what should I work on?" → `chisel ready --json`
- User wants to track a new task → `chisel create "..." --json`
- User says they finished something → `chisel close ID --reason "..." --json`
- User has a large feature to build → `chisel create` + `chisel decompose`
- User mentions something is blocked → `chisel dep add`

## Command Reference

### Finding Work

```bash
# Get unblocked tasks sorted by priority (most important command)
chisel ready --json

# List all tasks with filters
chisel list --status open --json
chisel list --status open --priority 1 --json
chisel list --type bug --json
```

### Creating Tasks

```bash
# Basic task
chisel create "Fix login bug" --json

# With options
chisel create "Implement OAuth" \
  -t task \
  -p 1 \
  -d "Add Google and GitHub OAuth providers" \
  --points 5 \
  --json

# Bug report
chisel create "Login fails with special chars" -t bug -p 0 --json
```

**Options:**
- `-t, --type`: task (default), epic, bug, spike, chore
- `-p, --priority`: 0 (critical), 1 (high), 2 (medium/default), 3 (low), 4 (backlog)
- `-d, --description`: Detailed description
- `--points`: Story points estimate
- `--labels`: Comma-separated labels
- `--parent`: Parent task ID for subtasks

### Updating Tasks

```bash
# Start working on a task
chisel update ch-abc123 --status in_progress --json

# Change priority
chisel update ch-abc123 --priority 0 --json

# Mark as blocked
chisel update ch-abc123 --status blocked --json
```

**Statuses:** open, in_progress, blocked, review, done, cancelled

### Completing Tasks

```bash
# Close with reason (always include a reason)
chisel close ch-abc123 --reason "Implemented feature with tests" --json

# Reopen if needed
chisel reopen ch-abc123 --json
```

### Breaking Down Large Tasks

For tasks >8 story points, decompose into subtasks:

```bash
# Create epic first
chisel create "User Dashboard" -t epic -p 1 --json
# Returns: {"task": {"id": "ch-abc123", ...}}

# Decompose into subtasks with story points
chisel decompose ch-abc123 \
  "Design dashboard layout" \
  "Build activity feed component" \
  "Implement settings panel" \
  "Write tests" \
  --points 2,5,5,3 \
  --json

# View the hierarchy
chisel tree ch-abc123 --json
```

### Managing Dependencies

```bash
# Task B is blocked by Task A (B cannot start until A is done)
chisel dep add ch-taskB --blocked-by ch-taskA --json

# Remove dependency
chisel dep remove ch-taskB ch-taskA --json

# See what's blocked
chisel blocked --json

# See dependencies for a specific task
chisel dep list ch-taskB --json
```

### Task Details

```bash
# Show full task details including dependencies
chisel show ch-abc123 --json
```

## JSON Response Format

### Successful Task Operation
```json
{
  "task": {
    "id": "ch-abc123",
    "title": "Fix login bug",
    "status": "open",
    "priority": 1,
    "task_type": "bug",
    "story_points": 3,
    "parent_id": null,
    "labels": ["auth"],
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  },
  "message": "Created task ch-abc123"
}
```

### Task List
```json
{
  "tasks": [
    {"id": "ch-abc123", "title": "Task 1", "priority": 1, "status": "open", ...},
    {"id": "ch-def456", "title": "Task 2", "priority": 2, "status": "open", ...}
  ]
}
```

### Error
```json
{
  "error": "Task ch-xyz not found"
}
```

## Standard Workflow

### 1. Starting a Session
```bash
chisel ready --json  # Find what to work on
```

### 2. Beginning a Task
```bash
chisel update ch-abc123 --status in_progress --json
chisel show ch-abc123 --json  # Get full details
```

### 3. Completing a Task
```bash
chisel close ch-abc123 --reason "Description of what was done" --json
chisel ready --json  # Find next task
```

### 4. When Blocked
```bash
chisel dep add ch-current --blocked-by ch-blocker --json
chisel update ch-current --status blocked --json
chisel ready --json  # Work on something else
```

## Priority Guide

| Priority | Value | When to Use |
|----------|-------|-------------|
| Critical | 0 | Production down, security issues |
| High | 1 | Must do today |
| Medium | 2 | This week (default) |
| Low | 3 | When time permits |
| Backlog | 4 | Future consideration |

## Task Types

| Type | When to Use |
|------|-------------|
| `task` | Standard work item (default) |
| `epic` | Large feature to be decomposed |
| `bug` | Defect to fix |
| `spike` | Research/investigation |
| `chore` | Maintenance, tech debt |

## Important Rules

1. **Always use `--json`** for programmatic parsing
2. **Always check `chisel ready`** before starting work
3. **Always update status** when starting (`in_progress`) or finishing (`close`)
4. **Always include `--reason`** when closing tasks
5. **Decompose large tasks** (>8 points) into subtasks
6. **Add dependencies** when tasks must be done in order
