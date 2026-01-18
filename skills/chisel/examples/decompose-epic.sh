#!/bin/bash
# Example: Breaking down an epic into subtasks

# Create an epic for a new feature
echo "Creating epic..."
EPIC_RESULT=$(chisel create "User Authentication System" -t epic -p 1 \
  -d "Implement complete user authentication with OAuth and session management" \
  --json)

EPIC_ID=$(echo "$EPIC_RESULT" | jq -r '.task.id')
echo "Created epic: $EPIC_ID"

# Decompose into subtasks with story points
echo "Decomposing into subtasks..."
chisel decompose "$EPIC_ID" \
  "Set up OAuth providers (Google, GitHub)" \
  "Create login/signup UI components" \
  "Implement session management" \
  "Add password reset flow" \
  "Write integration tests" \
  "Update API documentation" \
  --points 3,5,5,3,3,2 \
  --json

# View the resulting tree
echo "Task hierarchy:"
chisel tree "$EPIC_ID" --json | jq '.'

# Check ready tasks
echo "Ready tasks:"
chisel ready --json | jq '.tasks[] | {id, title, priority}'
