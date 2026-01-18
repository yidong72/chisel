# Chisel Command Reference

## Global Options

- `--project PATH`: Override project path
- `--json`: JSON output (recommended for agents)

## Project

```bash
chisel init [--json]     # Initialize project
chisel info [--json]     # Show project info
```

## Tasks

```bash
chisel create "Title" [options] [--json]
  -t, --type TYPE       # task, epic, bug, spike, chore
  -p, --priority N      # 0-4 (default: 2)
  -d, --description     # Description
  --parent ID           # Parent task ID
  --points N            # Story points
  --labels TEXT         # Comma-separated labels

chisel list [--status S] [--priority N] [--type T] [--limit N] [--json]
chisel show ID [--json]
chisel update ID [--title T] [-s STATUS] [-p N] [--labels L] [--json]
chisel close ID [--reason TEXT] [--json]
chisel reopen ID [--json]
chisel ready [--limit N] [--json]
chisel blocked [--json]
```

## Decomposition

```bash
chisel decompose ID "Sub1" "Sub2" [--points N,N] [--json]
chisel tree ID [--json]
```

## Dependencies

```bash
chisel dep add TASK_ID --blocked-by BLOCKER_ID [--json]
chisel dep remove TASK_ID BLOCKER_ID [--json]
chisel dep list TASK_ID [--json]
```

## Hooks

```bash
chisel hook set EVENT COMMAND [--json]   # Events: pre-close, post-create
chisel hook list [--event E] [--json]
chisel hook remove HOOK_ID [--json]
chisel validate ID [--json]              # Run pre-close hooks
```

## JSON Responses

```json
{"task": {...}, "message": "Created task ch-abc"}  // Single task
{"tasks": [...]}                                    // List
{"error": "Task not found"}                         // Error
```

## Exit Codes

- `0`: Success
- `1`: Error
