---
name: chisel
description: Use this skill for managing tasks, breaking down work, or tracking progress.

<example>
user: "What should I work on next?"
assistant: Runs `chisel ready --json` to find unblocked, prioritized work.
</example>

<example>
user: "I need to add authentication"
assistant: Creates epic with `chisel create`, then decomposes with `chisel decompose`.
</example>

<example>
user: "I'm done with the login feature"
assistant: Closes task with `chisel close ID --reason "..."`, then runs `chisel ready`.
</example>
---

# Chisel Skill

CLI: `chisel` (all commands support `--json`)

## Commands

| Command | Purpose |
|---------|---------|
| `chisel ready --json` | Find next task (unblocked, by priority) |
| `chisel create "Title" -p 1 --json` | Create task |
| `chisel update ID -s in_progress --json` | Update status |
| `chisel close ID --reason "Done" --json` | Complete task |
| `chisel decompose ID "Sub1" "Sub2" --json` | Break down task |
| `chisel tree ID --json` | View hierarchy |
| `chisel dep add B --blocked-by A --json` | Add dependency |
| `chisel blocked --json` | Show blocked tasks |
| `chisel validate ID --json` | Run quality hooks |

## Priority: 0 (critical) → 4 (backlog), default 2

## Types: `task`, `epic`, `bug`, `spike`, `chore`

## Workflow

```bash
chisel ready --json                    # Find work
chisel update ID -s in_progress --json # Start
chisel close ID --reason "..." --json  # Complete
```

## Breaking Down Epics

```bash
chisel create "Feature" -t epic -p 1 --json
chisel decompose ID "Design" "Implement" "Test" --points 2,5,3 --json
```

## Dependencies

```bash
chisel dep add B --blocked-by A --json  # B waits for A
chisel blocked --json                    # See what's blocked
```
