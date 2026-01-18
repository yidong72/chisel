"""CLI for Chisel task manager."""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from chisel.models import Task
from chisel.storage import Storage, get_storage, init_project
from chisel.utils import find_chisel_root, format_json_output, format_priority, format_status, truncate_string


def get_storage_or_exit(project_path: Optional[str] = None) -> Storage:
    """Get storage instance or exit with error."""
    path = Path(project_path) if project_path else None
    storage = get_storage(path)
    
    if storage is None:
        click.echo("Error: Not in a chisel project. Run 'chisel init' first.", err=True)
        sys.exit(1)
    
    return storage


def output_result(data: dict, as_json: bool):
    """Output result as JSON or human-readable format."""
    if as_json:
        click.echo(format_json_output(data))
    else:
        # Human-readable output depends on the data type
        if "task" in data:
            _print_task(data["task"])
        elif "tasks" in data:
            _print_task_list(data["tasks"])
        elif "message" in data:
            click.echo(data["message"])
        elif "error" in data:
            click.echo(f"Error: {data['error']}", err=True)
        else:
            click.echo(format_json_output(data))


def _print_task(task: dict):
    """Print a single task in human-readable format."""
    click.echo(f"\n{format_status(task['status'])} {task['id']}: {task['title']}")
    click.echo(f"   Type: {task['task_type']}  Priority: {format_priority(task['priority'])}")
    
    if task.get("description"):
        click.echo(f"   Description: {truncate_string(task['description'], 60)}")
    
    if task.get("parent_id"):
        click.echo(f"   Parent: {task['parent_id']}")
    
    if task.get("story_points"):
        click.echo(f"   Story Points: {task['story_points']}")
    
    if task.get("assignee"):
        click.echo(f"   Assignee: {task['assignee']}")
    
    if task.get("labels"):
        click.echo(f"   Labels: {', '.join(task['labels'])}")
    
    if task.get("acceptance_criteria"):
        click.echo("   Acceptance Criteria:")
        for i, criterion in enumerate(task["acceptance_criteria"], 1):
            click.echo(f"     {i}. {criterion}")
    
    click.echo(f"   Created: {task['created_at']}")
    if task.get("due_at"):
        click.echo(f"   Due: {task['due_at']}")
    click.echo()


def _print_task_list(tasks: list[dict]):
    """Print a list of tasks in human-readable format."""
    if not tasks:
        click.echo("No tasks found.")
        return
    
    click.echo(f"\n{'ID':<12} {'Status':<12} {'Pri':<8} {'Title':<40}")
    click.echo("-" * 76)
    
    for task in tasks:
        status_str = task["status"][:10]
        title_str = truncate_string(task["title"], 40)
        click.echo(f"{task['id']:<12} {status_str:<12} P{task['priority']:<6} {title_str:<40}")
    
    click.echo(f"\nTotal: {len(tasks)} task(s)")


# =============================================================================
# Main CLI Group
# =============================================================================

@click.group()
@click.option("--project", "-p", type=click.Path(exists=True), help="Project path override")
@click.pass_context
def main(ctx, project):
    """Chisel - Lightweight agent task manager."""
    ctx.ensure_object(dict)
    ctx.obj["project"] = project


# =============================================================================
# Project Commands
# =============================================================================

@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def init(ctx, as_json):
    """Initialize a new chisel project in the current directory."""
    project_path = Path(ctx.obj.get("project") or Path.cwd())
    chisel_dir = project_path / ".chisel"
    
    if chisel_dir.exists():
        output_result({"error": "Project already initialized"}, as_json)
        sys.exit(1)
    
    storage = init_project(project_path)
    
    output_result({
        "message": f"Initialized chisel project in {project_path}",
        "project_root": str(project_path),
        "database": str(chisel_dir / "chisel.db"),
    }, as_json)


@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def info(ctx, as_json):
    """Show current project information."""
    project_path = Path(ctx.obj.get("project")) if ctx.obj.get("project") else None
    
    if project_path:
        root = project_path
    else:
        root = find_chisel_root()
    
    if root is None:
        output_result({"error": "Not in a chisel project"}, as_json)
        sys.exit(1)
    
    storage = get_storage(root)
    config = storage.get_all_config() if storage else {}
    
    output_result({
        "project_root": str(root),
        "database": str(root / ".chisel" / "chisel.db"),
        "config": config,
    }, as_json)


# =============================================================================
# Task Commands
# =============================================================================

@main.command()
@click.argument("title")
@click.option("-t", "--type", "task_type", default="task", help="Task type (task, epic, bug, spike, chore)")
@click.option("-p", "--priority", type=int, default=2, help="Priority (0=critical, 1=high, 2=medium, 3=low, 4=backlog)")
@click.option("-d", "--description", default="", help="Task description")
@click.option("--parent", "parent_id", help="Parent task ID")
@click.option("--points", "story_points", type=int, help="Story points")
@click.option("--estimate", "estimated_minutes", type=int, help="Time estimate in minutes")
@click.option("--assignee", help="Task assignee")
@click.option("--labels", help="Comma-separated labels")
@click.option("--criteria", multiple=True, help="Acceptance criteria (can be repeated)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def create(ctx, title, task_type, priority, description, parent_id, story_points, 
           estimated_minutes, assignee, labels, criteria, as_json):
    """Create a new task."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    # Parse labels
    label_list = [l.strip() for l in labels.split(",")] if labels else []
    
    task = storage.create_task(
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
        story_points=story_points,
        estimated_minutes=estimated_minutes,
        parent_id=parent_id,
        acceptance_criteria=list(criteria),
        assignee=assignee,
        labels=label_list,
    )
    
    output_result({"task": task.to_dict(), "message": f"Created task {task.id}"}, as_json)


@main.command("list")
@click.option("--status", help="Filter by status")
@click.option("--priority", type=int, help="Filter by priority")
@click.option("--type", "task_type", help="Filter by task type")
@click.option("--parent", "parent_id", help="Filter by parent task ID")
@click.option("--assignee", help="Filter by assignee")
@click.option("--labels", help="Filter by labels (comma-separated)")
@click.option("--limit", type=int, help="Maximum number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_tasks(ctx, status, priority, task_type, parent_id, assignee, labels, limit, as_json):
    """List tasks with optional filters."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    label_list = [l.strip() for l in labels.split(",")] if labels else None
    
    tasks = storage.list_tasks(
        status=status,
        priority=priority,
        task_type=task_type,
        parent_id=parent_id,
        assignee=assignee,
        labels=label_list,
        limit=limit,
    )
    
    output_result({"tasks": [t.to_dict() for t in tasks]}, as_json)


@main.command()
@click.argument("task_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def show(ctx, task_id, as_json):
    """Show detailed information about a task."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    task = storage.get_task(task_id)
    if task is None:
        output_result({"error": f"Task {task_id} not found"}, as_json)
        sys.exit(1)
    
    # Get additional info
    dependencies = storage.get_dependencies(task_id)
    dependents = storage.get_dependents(task_id)
    children = storage.get_children(task_id) if task.task_type == "epic" else []
    
    result = {
        "task": task.to_dict(),
        "dependencies": [d.to_dict() for d in dependencies],
        "dependents": [d.to_dict() for d in dependents],
        "children": [c.to_dict() for c in children],
    }
    
    if as_json:
        click.echo(format_json_output(result))
    else:
        _print_task(result["task"])
        
        if dependencies:
            click.echo("   Blocked by:")
            for dep in dependencies:
                blocker = storage.get_task(dep.depends_on_id)
                blocker_title = blocker.title if blocker else "Unknown"
                click.echo(f"     - {dep.depends_on_id}: {truncate_string(blocker_title, 40)}")
        
        if dependents:
            click.echo("   Blocks:")
            for dep in dependents:
                dependent = storage.get_task(dep.task_id)
                dependent_title = dependent.title if dependent else "Unknown"
                click.echo(f"     - {dep.task_id}: {truncate_string(dependent_title, 40)}")
        
        if children:
            click.echo("   Subtasks:")
            for child in children:
                click.echo(f"     {format_status(child.status)} {child.id}: {truncate_string(child.title, 40)}")


@main.command()
@click.argument("task_id")
@click.option("--title", help="New title")
@click.option("--description", "-d", help="New description")
@click.option("--type", "task_type", help="New task type")
@click.option("--priority", "-p", type=int, help="New priority")
@click.option("--status", "-s", help="New status")
@click.option("--points", "story_points", type=int, help="Story points")
@click.option("--estimate", "estimated_minutes", type=int, help="Time estimate in minutes")
@click.option("--assignee", help="Task assignee")
@click.option("--labels", help="Comma-separated labels (replaces existing)")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def update(ctx, task_id, title, description, task_type, priority, status, 
           story_points, estimated_minutes, assignee, labels, as_json):
    """Update a task."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    # Check task exists
    existing = storage.get_task(task_id)
    if existing is None:
        output_result({"error": f"Task {task_id} not found"}, as_json)
        sys.exit(1)
    
    # Parse labels if provided
    label_list = [l.strip() for l in labels.split(",")] if labels else None
    
    task = storage.update_task(
        task_id,
        title=title,
        description=description,
        task_type=task_type,
        priority=priority,
        status=status,
        story_points=story_points,
        estimated_minutes=estimated_minutes,
        assignee=assignee,
        labels=label_list,
    )
    
    output_result({"task": task.to_dict(), "message": f"Updated task {task_id}"}, as_json)


@main.command()
@click.argument("task_id")
@click.option("--reason", help="Reason for closing")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def close(ctx, task_id, reason, as_json):
    """Close a task (mark as done)."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    # Check task exists
    existing = storage.get_task(task_id)
    if existing is None:
        output_result({"error": f"Task {task_id} not found"}, as_json)
        sys.exit(1)
    
    # Run pre-close hooks
    from chisel.hooks import run_hooks
    hook_results = run_hooks(storage, "pre-close", task_id)
    
    if any(not r["success"] for r in hook_results):
        failed = [r for r in hook_results if not r["success"]]
        output_result({
            "error": "Pre-close hooks failed",
            "hook_results": hook_results,
        }, as_json)
        sys.exit(1)
    
    # Update task status
    description = existing.description
    if reason:
        description = f"{description}\n\nClosed: {reason}" if description else f"Closed: {reason}"
    
    task = storage.update_task(task_id, status="done", description=description)
    
    # Update parent status if needed
    from chisel.decompose import update_parent_status
    update_parent_status(storage, task_id)
    
    output_result({
        "task": task.to_dict(),
        "message": f"Closed task {task_id}",
        "hook_results": hook_results,
    }, as_json)


@main.command()
@click.argument("task_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def reopen(ctx, task_id, as_json):
    """Reopen a closed or cancelled task."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    existing = storage.get_task(task_id)
    if existing is None:
        output_result({"error": f"Task {task_id} not found"}, as_json)
        sys.exit(1)
    
    if existing.status not in ("done", "cancelled"):
        output_result({"error": f"Task {task_id} is not closed or cancelled"}, as_json)
        sys.exit(1)
    
    task = storage.update_task(task_id, status="open")
    
    output_result({"task": task.to_dict(), "message": f"Reopened task {task_id}"}, as_json)


@main.command()
@click.option("--limit", type=int, default=10, help="Maximum number of results")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def ready(ctx, limit, as_json):
    """Show tasks ready to work on (no blockers)."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    tasks = storage.get_ready_tasks(limit=limit)
    
    output_result({"tasks": [t.to_dict() for t in tasks]}, as_json)


@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def blocked(ctx, as_json):
    """Show tasks that are blocked."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    tasks = storage.get_blocked_tasks()
    
    # Add blocker info
    task_data = []
    for task in tasks:
        data = task.to_dict()
        deps = storage.get_dependencies(task.id)
        blockers = []
        for dep in deps:
            if dep.dep_type == "blocks":
                blocker = storage.get_task(dep.depends_on_id)
                if blocker and blocker.status not in ("done", "cancelled"):
                    blockers.append({
                        "id": blocker.id,
                        "title": blocker.title,
                        "status": blocker.status,
                    })
        data["blocked_by"] = blockers
        task_data.append(data)
    
    output_result({"tasks": task_data}, as_json)


# =============================================================================
# Dependency Commands
# =============================================================================

@main.group()
def dep():
    """Manage task dependencies."""
    pass


@dep.command("add")
@click.argument("task_id")
@click.option("--blocked-by", "blocked_by", required=True, help="Task ID that blocks this task")
@click.option("--type", "dep_type", default="blocks", help="Dependency type")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def dep_add(ctx, task_id, blocked_by, dep_type, as_json):
    """Add a dependency (task_id is blocked by blocked_by)."""
    storage = get_storage_or_exit(ctx.parent.parent.obj.get("project"))
    
    # Verify both tasks exist
    task = storage.get_task(task_id)
    blocker = storage.get_task(blocked_by)
    
    if task is None:
        output_result({"error": f"Task {task_id} not found"}, as_json)
        sys.exit(1)
    
    if blocker is None:
        output_result({"error": f"Task {blocked_by} not found"}, as_json)
        sys.exit(1)
    
    # Prevent self-dependency
    if task_id == blocked_by:
        output_result({"error": "Task cannot depend on itself"}, as_json)
        sys.exit(1)
    
    try:
        dependency = storage.add_dependency(task_id, blocked_by, dep_type)
        output_result({
            "dependency": dependency.to_dict(),
            "message": f"Added dependency: {task_id} blocked by {blocked_by}",
        }, as_json)
    except Exception as e:
        output_result({"error": f"Failed to add dependency: {e}"}, as_json)
        sys.exit(1)


@dep.command("remove")
@click.argument("task_id")
@click.argument("blocked_by")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def dep_remove(ctx, task_id, blocked_by, as_json):
    """Remove a dependency."""
    storage = get_storage_or_exit(ctx.parent.parent.obj.get("project"))
    
    removed = storage.remove_dependency(task_id, blocked_by)
    
    if removed:
        output_result({"message": f"Removed dependency: {task_id} no longer blocked by {blocked_by}"}, as_json)
    else:
        output_result({"error": "Dependency not found"}, as_json)
        sys.exit(1)


@dep.command("list")
@click.argument("task_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def dep_list(ctx, task_id, as_json):
    """List dependencies for a task."""
    storage = get_storage_or_exit(ctx.parent.parent.obj.get("project"))
    
    task = storage.get_task(task_id)
    if task is None:
        output_result({"error": f"Task {task_id} not found"}, as_json)
        sys.exit(1)
    
    dependencies = storage.get_dependencies(task_id)
    dependents = storage.get_dependents(task_id)
    
    output_result({
        "task_id": task_id,
        "blocked_by": [d.to_dict() for d in dependencies],
        "blocks": [d.to_dict() for d in dependents],
    }, as_json)


# =============================================================================
# Decomposition Commands
# =============================================================================

@main.command()
@click.argument("task_id")
@click.argument("subtasks", nargs=-1, required=True)
@click.option("--points", help="Comma-separated story points for each subtask")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def decompose(ctx, task_id, subtasks, points, as_json):
    """Break down a task into subtasks."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    from chisel.decompose import decompose_task
    
    # Parse points
    point_list = None
    if points:
        try:
            point_list = [int(p.strip()) for p in points.split(",")]
            if len(point_list) != len(subtasks):
                output_result({"error": "Number of points must match number of subtasks"}, as_json)
                sys.exit(1)
        except ValueError:
            output_result({"error": "Invalid points format"}, as_json)
            sys.exit(1)
    
    result = decompose_task(storage, task_id, list(subtasks), point_list)
    
    if "error" in result:
        output_result(result, as_json)
        sys.exit(1)
    
    output_result(result, as_json)


@main.command()
@click.argument("task_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def tree(ctx, task_id, as_json):
    """Show task hierarchy tree."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    from chisel.decompose import get_task_tree
    
    result = get_task_tree(storage, task_id)
    
    if "error" in result:
        output_result(result, as_json)
        sys.exit(1)
    
    if as_json:
        click.echo(format_json_output(result))
    else:
        _print_tree(result["tree"], 0)


def _print_tree(node: dict, level: int):
    """Print a task tree recursively."""
    indent = "  " * level
    prefix = "└─ " if level > 0 else ""
    task = node["task"]
    click.echo(f"{indent}{prefix}{format_status(task['status'])} {task['id']}: {task['title']}")
    
    for child in node.get("children", []):
        _print_tree(child, level + 1)


# =============================================================================
# Hook Commands
# =============================================================================

@main.group()
def hook():
    """Manage quality hooks."""
    pass


@hook.command("set")
@click.argument("event")
@click.argument("command")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def hook_set(ctx, event, command, as_json):
    """Add a hook for an event (pre-close, post-create, etc.)."""
    storage = get_storage_or_exit(ctx.parent.parent.obj.get("project"))
    
    hook_obj = storage.add_hook(event, command)
    
    output_result({
        "hook": hook_obj.to_dict(),
        "message": f"Added hook for {event}: {command}",
    }, as_json)


@hook.command("list")
@click.option("--event", help="Filter by event")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def hook_list(ctx, event, as_json):
    """List configured hooks."""
    storage = get_storage_or_exit(ctx.parent.parent.obj.get("project"))
    
    hooks = storage.get_hooks(event)
    
    if as_json:
        click.echo(format_json_output({"hooks": [h.to_dict() for h in hooks]}))
    else:
        if not hooks:
            click.echo("No hooks configured.")
            return
        
        click.echo(f"\n{'ID':<6} {'Event':<15} {'Enabled':<10} {'Command':<40}")
        click.echo("-" * 75)
        
        for h in hooks:
            enabled = "Yes" if h.enabled else "No"
            click.echo(f"{h.id:<6} {h.event:<15} {enabled:<10} {truncate_string(h.command, 40):<40}")


@hook.command("remove")
@click.argument("hook_id", type=int)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def hook_remove(ctx, hook_id, as_json):
    """Remove a hook by ID."""
    storage = get_storage_or_exit(ctx.parent.parent.obj.get("project"))
    
    removed = storage.remove_hook(hook_id)
    
    if removed:
        output_result({"message": f"Removed hook {hook_id}"}, as_json)
    else:
        output_result({"error": f"Hook {hook_id} not found"}, as_json)
        sys.exit(1)


@main.command()
@click.argument("task_id")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def validate(ctx, task_id, as_json):
    """Run validation hooks for a task."""
    storage = get_storage_or_exit(ctx.obj.get("project"))
    
    task = storage.get_task(task_id)
    if task is None:
        output_result({"error": f"Task {task_id} not found"}, as_json)
        sys.exit(1)
    
    from chisel.hooks import run_hooks
    
    # Run pre-close hooks as validation
    results = run_hooks(storage, "pre-close", task_id)
    
    all_passed = all(r["success"] for r in results)
    
    output_result({
        "task_id": task_id,
        "valid": all_passed,
        "hook_results": results,
    }, as_json)
    
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
