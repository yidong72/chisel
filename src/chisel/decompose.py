"""Task decomposition for Chisel task manager."""

from typing import Optional

from chisel.models import Task
from chisel.storage import Storage


def decompose_task(
    storage: Storage,
    parent_id: str,
    subtask_titles: list[str],
    story_points: Optional[list[int]] = None,
) -> dict:
    """Break down a task into subtasks.
    
    Args:
        storage: Storage instance
        parent_id: Parent task ID to decompose
        subtask_titles: List of subtask titles
        story_points: Optional list of story points for each subtask
    
    Returns:
        Dictionary with parent task and created subtasks
    """
    # Get parent task
    parent = storage.get_task(parent_id)
    if parent is None:
        return {"error": f"Task {parent_id} not found"}
    
    # Create subtasks
    subtasks = []
    for i, title in enumerate(subtask_titles):
        points = story_points[i] if story_points and i < len(story_points) else None
        
        subtask = storage.create_task(
            title=title,
            task_type="task",
            priority=parent.priority,
            parent_id=parent_id,
            story_points=points,
        )
        subtasks.append(subtask)
    
    # Update parent to epic type if not already
    if parent.task_type != "epic":
        storage.update_task(parent_id, task_type="epic")
        parent = storage.get_task(parent_id)
    
    return {
        "parent": parent.to_dict(),
        "subtasks": [s.to_dict() for s in subtasks],
        "message": f"Created {len(subtasks)} subtasks under {parent_id}",
    }


def get_task_tree(storage: Storage, task_id: str) -> dict:
    """Get the full task hierarchy tree.
    
    Args:
        storage: Storage instance
        task_id: Root task ID
    
    Returns:
        Dictionary with nested task tree structure
    """
    task = storage.get_task(task_id)
    if task is None:
        return {"error": f"Task {task_id} not found"}
    
    tree = _build_tree_node(storage, task)
    
    return {"tree": tree}


def _build_tree_node(storage: Storage, task: Task) -> dict:
    """Build a tree node for a task.
    
    Args:
        storage: Storage instance
        task: Task object
    
    Returns:
        Dictionary with task and children
    """
    children = storage.get_children(task.id)
    
    child_nodes = [_build_tree_node(storage, child) for child in children]
    
    return {
        "task": task.to_dict(),
        "children": child_nodes,
    }


def update_parent_status(storage: Storage, task_id: str):
    """Update parent task status based on children completion.
    
    When all children are done, parent is marked done.
    When any child is in progress, parent is marked in progress.
    
    Args:
        storage: Storage instance
        task_id: Task ID that was just updated
    """
    task = storage.get_task(task_id)
    if task is None or task.parent_id is None:
        return
    
    parent_id = task.parent_id
    children = storage.get_children(parent_id)
    
    if not children:
        return
    
    # Check children statuses
    all_done = all(c.status in ("done", "cancelled") for c in children)
    any_in_progress = any(c.status == "in_progress" for c in children)
    
    parent = storage.get_task(parent_id)
    if parent is None:
        return
    
    # Update parent status
    if all_done:
        storage.update_task(parent_id, status="done")
    elif any_in_progress and parent.status == "open":
        storage.update_task(parent_id, status="in_progress")
    
    # Recursively update grandparent
    update_parent_status(storage, parent_id)


def get_subtask_progress(storage: Storage, parent_id: str) -> dict:
    """Get progress information for subtasks.
    
    Args:
        storage: Storage instance
        parent_id: Parent task ID
    
    Returns:
        Dictionary with progress statistics
    """
    task = storage.get_task(parent_id)
    if task is None:
        return {"error": f"Task {parent_id} not found"}
    
    children = storage.get_children(parent_id)
    
    if not children:
        return {
            "parent_id": parent_id,
            "total": 0,
            "done": 0,
            "in_progress": 0,
            "open": 0,
            "blocked": 0,
            "cancelled": 0,
            "progress_percent": 0,
            "total_points": 0,
            "completed_points": 0,
        }
    
    # Count by status
    status_counts = {
        "done": 0,
        "in_progress": 0,
        "open": 0,
        "blocked": 0,
        "cancelled": 0,
        "review": 0,
    }
    
    total_points = 0
    completed_points = 0
    
    for child in children:
        status = child.status
        if status in status_counts:
            status_counts[status] += 1
        
        if child.story_points:
            total_points += child.story_points
            if child.status == "done":
                completed_points += child.story_points
    
    total = len(children)
    done = status_counts["done"]
    
    # Calculate progress (done / non-cancelled)
    countable = total - status_counts["cancelled"]
    progress_percent = (done / countable * 100) if countable > 0 else 0
    
    return {
        "parent_id": parent_id,
        "total": total,
        **status_counts,
        "progress_percent": round(progress_percent, 1),
        "total_points": total_points,
        "completed_points": completed_points,
    }


def suggest_decomposition(task: Task) -> list[str]:
    """Suggest subtask titles based on task type and title.
    
    This is a simple heuristic-based suggestion. AI agents can provide
    better decomposition through their own analysis.
    
    Args:
        task: Task to decompose
    
    Returns:
        List of suggested subtask titles
    """
    suggestions = []
    
    # Common patterns for different task types
    if task.task_type == "epic" or task.story_points and task.story_points > 8:
        # Large tasks often follow: Design, Implement, Test pattern
        base = task.title.replace("Implement ", "").replace("Add ", "").replace("Create ", "")
        suggestions = [
            f"Design {base}",
            f"Implement {base}",
            f"Write tests for {base}",
            f"Document {base}",
        ]
    elif "API" in task.title or "endpoint" in task.title.lower():
        suggestions = [
            "Define API schema",
            "Implement endpoint handler",
            "Add input validation",
            "Write integration tests",
            "Update API documentation",
        ]
    elif "UI" in task.title or "component" in task.title.lower():
        suggestions = [
            "Create component structure",
            "Implement styling",
            "Add interactivity",
            "Write component tests",
            "Add accessibility features",
        ]
    elif task.task_type == "bug":
        suggestions = [
            "Reproduce the bug",
            "Identify root cause",
            "Implement fix",
            "Add regression test",
        ]
    
    return suggestions
