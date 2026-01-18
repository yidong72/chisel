# Quick Start Guide

Get up and running with Chisel in 5 minutes.

## Installation

```bash
pip install chisel-tasks
```

## Initialize a Project

Navigate to your project root and initialize Chisel:

```bash
cd my-project
chisel init
```

This creates a `.chisel/` directory with the SQLite database.

## Create Your First Task

```bash
chisel create "Set up project structure" -p 1
```

Options:
- `-p 1`: High priority (0=critical, 1=high, 2=medium, 3=low, 4=backlog)
- `-t bug`: Task type (task, epic, bug, spike, chore)
- `-d "Description"`: Add a description

## Find Work to Do

```bash
chisel ready
```

Shows tasks that are open and have no blockers, sorted by priority.

## Start Working

```bash
chisel update ch-abc123 --status in_progress
```

## Complete a Task

```bash
chisel close ch-abc123 --reason "Implemented the feature"
```

## Break Down Large Tasks

For tasks that are too big (>8 story points), decompose them:

```bash
# Create an epic
chisel create "Build API" -t epic -p 1

# Break it down
chisel decompose ch-epic123 \
  "Design API schema" \
  "Implement endpoints" \
  "Add authentication" \
  "Write tests" \
  --points 2,5,3,3
```

## Add Dependencies

When task B requires task A to be completed first:

```bash
chisel dep add ch-taskB --blocked-by ch-taskA
```

Now task B won't appear in `chisel ready` until task A is done.

## Set Up Quality Hooks

Add commands that run before closing tasks:

```bash
chisel hook set pre-close "pytest tests/ -q"
chisel hook set pre-close "ruff check ."
```

Now when you close a task, these commands run first. The task won't close if they fail.

## For AI Agents

Always use `--json` for machine-readable output:

```bash
chisel ready --json
chisel create "Task title" --json
chisel close ch-abc123 --json
```

## Next Steps

- Read the [CLI Reference](cli-reference.md) for all commands
- See [Workflow Patterns](workflow-patterns.md) for common workflows
- Check [AGENTS.md](../AGENTS.md) for AI agent integration
