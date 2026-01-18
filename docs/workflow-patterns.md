# Workflow Patterns

Common patterns for using Chisel effectively.

## Daily Workflow

### Start of Day

```bash
# See what's ready to work on
chisel ready --limit 10

# Pick the highest priority item and start
chisel update ch-abc123 --status in_progress
```

### During Work

```bash
# Check task details
chisel show ch-abc123

# If you discover related work
chisel create "Found: Need to refactor X" -p 2

# If current task is blocked by new discovery
chisel dep add ch-abc123 --blocked-by ch-newwork
chisel update ch-abc123 --status blocked
```

### End of Task

```bash
# Validate (runs hooks)
chisel validate ch-abc123

# Close with context
chisel close ch-abc123 --reason "Implemented feature X with tests"

# Find next task
chisel ready
```

## Feature Development

### Planning a Feature

```bash
# Create the epic
chisel create "User Dashboard" -t epic -p 1 \
  -d "Create a user dashboard with activity feed and settings"

# Decompose into manageable subtasks
chisel decompose ch-epic123 \
  "Design dashboard layout" \
  "Create activity feed component" \
  "Implement settings panel" \
  "Add data fetching layer" \
  "Write component tests" \
  --points 2,5,5,3,3
```

### Working Through an Epic

```bash
# Get the next subtask
chisel ready

# Start working
chisel update ch-sub1 --status in_progress

# Complete and move on
chisel close ch-sub1 --reason "Layout designed, mockups approved"
chisel ready  # Get next subtask
```

### Tracking Progress

```bash
# View epic tree to see progress
chisel tree ch-epic123

# Check what's blocked
chisel blocked
```

## Bug Triage

### Creating Bug Reports

```bash
# High priority bug
chisel create "Login fails with special characters" \
  -t bug -p 1 \
  -d "Users cannot log in if password contains < or >" \
  --labels "auth,security"

# Lower priority bug
chisel create "Alignment issue on mobile" \
  -t bug -p 3 \
  --labels "ui,mobile"
```

### Bug Fix Workflow

```bash
# Find bugs to fix
chisel list --type bug --status open

# Start working
chisel update ch-bug123 --status in_progress

# When fixed
chisel close ch-bug123 --reason "Fixed input sanitization, added regression test"
```

## Research/Spikes

### Planning Research

```bash
# Create a spike
chisel create "Investigate caching strategies" \
  -t spike -p 2 \
  -d "Research Redis vs Memcached for session storage" \
  --points 3

# Add acceptance criteria
chisel update ch-spike123 --criteria "Document pros/cons" \
  --criteria "Benchmark performance" \
  --criteria "Provide recommendation"
```

### Completing Research

```bash
# Document findings in the close reason
chisel close ch-spike123 \
  --reason "Recommend Redis. See docs/adr/003-caching.md for details"
```

## Managing Dependencies

### Linear Dependencies

When tasks must be done in sequence:

```bash
# Create tasks
chisel create "Set up database" -p 1
chisel create "Create user model" -p 1
chisel create "Build API endpoints" -p 1

# Set up chain
chisel dep add ch-model --blocked-by ch-database
chisel dep add ch-api --blocked-by ch-model

# Only database task appears in ready
chisel ready  # Shows only ch-database
```

### Parallel with Merge

When multiple tasks can be done in parallel, then one depends on all:

```bash
# Create parallel tasks
chisel create "Frontend component" -p 1
chisel create "Backend endpoint" -p 1
chisel create "Integration" -p 1

# Integration blocked by both
chisel dep add ch-integration --blocked-by ch-frontend
chisel dep add ch-integration --blocked-by ch-backend

# Both frontend and backend appear in ready
chisel ready  # Shows ch-frontend and ch-backend
```

## Quality Gates

### Setting Up Hooks

```bash
# Add test requirement
chisel hook set pre-close "pytest tests/ -q"

# Add linting
chisel hook set pre-close "ruff check ."

# Add type checking
chisel hook set pre-close "mypy src/"
```

### Validating Before Close

```bash
# Check if task would pass
chisel validate ch-abc123

# If validation fails, fix issues then retry
chisel close ch-abc123 --reason "Feature complete with tests"
```

## Team Workflow

### Assigning Work

```bash
# Create and assign
chisel create "Implement OAuth" -p 1 --assignee "alice"

# Reassign
chisel update ch-abc123 --assignee "bob"

# Find your tasks
chisel list --assignee "alice" --status open
```

### Using Labels

```bash
# Create with labels
chisel create "Update docs" -p 3 --labels "docs,tech-debt"

# Find by label
chisel list --labels "tech-debt"
```

## Maintenance Tasks

### Regular Chores

```bash
# Create recurring maintenance
chisel create "Update dependencies" -t chore -p 3

# Track tech debt
chisel create "Refactor authentication module" \
  -t chore -p 4 \
  --labels "tech-debt,auth"
```

### Backlog Management

```bash
# Review backlog
chisel list --priority 4 --status open

# Promote important items
chisel update ch-backlog --priority 2

# Archive stale items
chisel update ch-old --status cancelled
```

## Integration with CI/CD

### In CI Pipeline

```bash
# Find task from branch name
TASK_ID=$(echo "$BRANCH_NAME" | grep -oP 'ch-[a-z0-9]+')

# Update status
chisel update "$TASK_ID" --status review

# Run validation
chisel validate "$TASK_ID"
```

### On Merge

```bash
# Close task
chisel close "$TASK_ID" --reason "Merged in PR #123"
```
