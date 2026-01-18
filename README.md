# Chisel - Agent Task Manager

Lightweight task manager designed for AI-assisted development. Chisel provides a simple CLI with JSON output that AI agents can use to manage work, track progress, and break down complex tasks.

## Features

- **Project-Based**: Each project has its own `.chisel/` directory (like `.git/`)
- **Auto-Discovery**: Walks up directory tree to find nearest project
- **Agent-Agnostic**: JSON output for all commands, works with any AI agent
- **Lightweight**: Single SQLite file, minimal dependencies
- **Flexible Workflow**: No mandatory phases, agents choose their approach
- **Quality Hooks**: Optional pre/post event commands
- **Task Decomposition**: Parent-child relationships, blocking dependencies

## Installation

```bash
pip install chisel-tasks
```

Or install from source:

```bash
git clone https://github.com/your-org/chisel.git
cd chisel
pip install -e .
```

## Quick Start

```bash
# Initialize a new project
chisel init

# Create tasks
chisel create "Implement user authentication" -p 1 --json
chisel create "Fix login bug" -t bug --json

# Find ready work (no blockers, by priority)
chisel ready --json

# Update task status
chisel update ch-abc123 --status in_progress --json

# Close a task
chisel close ch-abc123 --reason "Implemented OAuth" --json
```

## CLI Reference

### Project Commands

```bash
# Initialize project in current directory
chisel init [--json]

# Show project info
chisel info [--json]
```

### Task Commands

```bash
# Create a task
chisel create "Title" [-t type] [-p priority] [-d description] [--parent ID] [--json]

# List tasks
chisel list [--status open] [--priority 0-4] [--type bug] [--limit N] [--json]

# Show task details
chisel show ID [--json]

# Update a task
chisel update ID [--title "New"] [--status X] [--priority N] [--json]

# Close a task
chisel close ID [--reason "Done"] [--json]

# Reopen a task
chisel reopen ID [--json]

# Get ready tasks (no blockers)
chisel ready [--limit 5] [--json]

# Get blocked tasks
chisel blocked [--json]
```

### Decomposition Commands

```bash
# Break down a task into subtasks
chisel decompose ID "Subtask 1" "Subtask 2" [--points 2,3] [--json]

# View task tree
chisel tree ID [--json]
```

### Dependency Commands

```bash
# Add dependency (B blocked by A)
chisel dep add B --blocked-by A [--json]

# Remove dependency
chisel dep remove B A [--json]

# List dependencies for a task
chisel dep list ID [--json]
```

### Hook Commands

```bash
# Add a hook
chisel hook set pre-close "pytest tests/ -q"

# List hooks
chisel hook list [--json]

# Remove a hook
chisel hook remove HOOK_ID [--json]

# Validate a task (run hooks)
chisel validate ID [--json]
```

## Task Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Auto-generated ID (e.g., "ch-abc123") |
| `title` | string | Task title |
| `description` | string | Detailed description |
| `task_type` | string | task, epic, bug, spike, chore |
| `priority` | int | 0=critical, 1=high, 2=medium, 3=low, 4=backlog |
| `status` | string | open, in_progress, blocked, review, done, cancelled |
| `story_points` | int | Effort estimate |
| `parent_id` | string | Parent task ID (for subtasks) |
| `labels` | list | Tags/labels |
| `acceptance_criteria` | list | Completion criteria |

## Priority Levels

- **P0 (0)**: Critical - drop everything
- **P1 (1)**: High - do today
- **P2 (2)**: Medium - this week (default)
- **P3 (3)**: Low - when time permits
- **P4 (4)**: Backlog - someday

## Task Lifecycle

```
open -> in_progress -> review -> done
          |              |
          v              v
       blocked       cancelled
```

## Quality Hooks

Hooks run shell commands at specific events:

- `pre-close`: Before a task is closed (validation)
- `post-create`: After a task is created

Example setup:

```bash
chisel hook set pre-close "pytest tests/ -q"
chisel hook set pre-close "ruff check ."
```

Hooks receive the task ID via `CHISEL_TASK_ID` environment variable.

## Project Structure

```
my-project/
├── .chisel/                  # Created by chisel init
│   ├── chisel.db             # SQLite database
│   └── config.json           # Project config (optional)
├── src/
└── ...
```

## For AI Agents

All commands support `--json` for machine-readable output. Recommended workflow:

1. Use `chisel ready --json` to find the highest priority unblocked task
2. Update status: `chisel update ID --status in_progress --json`
3. Work on the task
4. Validate: `chisel validate ID --json`
5. Close: `chisel close ID --reason "Description" --json`

For complex tasks (>8 story points), use decomposition:

```bash
chisel decompose TASK-ID "Step 1" "Step 2" "Step 3" --points 3,5,2 --json
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=chisel
```

## License

MIT
