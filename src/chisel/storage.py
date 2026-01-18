"""SQLite storage layer for Chisel task manager."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Optional

from chisel.models import Dependency, Hook, Task
from chisel.utils import generate_task_id


# SQL Schema
SCHEMA = """
-- Core tables
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    task_type TEXT DEFAULT 'task',
    priority INTEGER DEFAULT 2,
    story_points INTEGER,
    estimated_minutes INTEGER,
    status TEXT DEFAULT 'open',
    parent_id TEXT REFERENCES tasks(id),
    acceptance_criteria TEXT,
    quality_score REAL,
    assignee TEXT,
    labels TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    due_at TEXT,
    defer_until TEXT
);

CREATE TABLE IF NOT EXISTS dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    depends_on_id TEXT NOT NULL REFERENCES tasks(id),
    dep_type TEXT DEFAULT 'blocks',
    created_at TEXT NOT NULL,
    UNIQUE(task_id, depends_on_id, dep_type)
);

CREATE TABLE IF NOT EXISTS hooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    command TEXT NOT NULL,
    enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_id);
CREATE INDEX IF NOT EXISTS idx_deps_task ON dependencies(task_id);
CREATE INDEX IF NOT EXISTS idx_deps_depends_on ON dependencies(depends_on_id);
"""


class Storage:
    """SQLite storage for tasks, dependencies, and hooks."""
    
    def __init__(self, db_path: Path):
        """Initialize storage with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create database schema if not exists."""
        with self._connection() as conn:
            conn.executescript(SCHEMA)
            conn.commit()
    
    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # =========================================================================
    # Task Operations
    # =========================================================================
    
    def create_task(
        self,
        title: str,
        description: str = "",
        task_type: str = "task",
        priority: int = 2,
        story_points: Optional[int] = None,
        estimated_minutes: Optional[int] = None,
        parent_id: Optional[str] = None,
        acceptance_criteria: Optional[list[str]] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
        due_at: Optional[datetime] = None,
        defer_until: Optional[datetime] = None,
        id_prefix: str = "ch",
    ) -> Task:
        """Create a new task.
        
        Args:
            title: Task title
            description: Task description
            task_type: Type of task (task, epic, bug, etc.)
            priority: Priority level (0-4)
            story_points: Story point estimate
            estimated_minutes: Time estimate in minutes
            parent_id: Parent task ID for subtasks
            acceptance_criteria: List of acceptance criteria
            assignee: Task assignee
            labels: List of labels
            due_at: Due date
            defer_until: Defer until date
            id_prefix: Prefix for generated ID
        
        Returns:
            Created Task object
        """
        task_id = generate_task_id(id_prefix)
        now = datetime.now()
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            story_points=story_points,
            estimated_minutes=estimated_minutes,
            status="open",
            parent_id=parent_id,
            acceptance_criteria=acceptance_criteria or [],
            quality_score=None,
            assignee=assignee,
            labels=labels or [],
            created_at=now,
            updated_at=now,
            due_at=due_at,
            defer_until=defer_until,
        )
        
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, title, description, task_type, priority,
                    story_points, estimated_minutes, status, parent_id,
                    acceptance_criteria, quality_score, assignee, labels,
                    created_at, updated_at, due_at, defer_until
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.id,
                    task.title,
                    task.description,
                    task.task_type,
                    task.priority,
                    task.story_points,
                    task.estimated_minutes,
                    task.status,
                    task.parent_id,
                    json.dumps(task.acceptance_criteria),
                    task.quality_score,
                    task.assignee,
                    json.dumps(task.labels),
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                    task.due_at.isoformat() if task.due_at else None,
                    task.defer_until.isoformat() if task.defer_until else None,
                ),
            )
            conn.commit()
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: Task ID
        
        Returns:
            Task object or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            ).fetchone()
            
            if row:
                return self._row_to_task(row)
            return None
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        task_type: Optional[str] = None,
        parent_id: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
        limit: Optional[int] = None,
    ) -> list[Task]:
        """List tasks with optional filters.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            task_type: Filter by task type
            parent_id: Filter by parent task
            assignee: Filter by assignee
            labels: Filter by labels (any match)
            limit: Maximum number of results
        
        Returns:
            List of matching tasks
        """
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list[Any] = []
        
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        
        if priority is not None:
            query += " AND priority = ?"
            params.append(priority)
        
        if task_type is not None:
            query += " AND task_type = ?"
            params.append(task_type)
        
        if parent_id is not None:
            query += " AND parent_id = ?"
            params.append(parent_id)
        
        if assignee is not None:
            query += " AND assignee = ?"
            params.append(assignee)
        
        if labels:
            # Check if any label matches
            label_conditions = " OR ".join(["labels LIKE ?" for _ in labels])
            query += f" AND ({label_conditions})"
            params.extend([f'%"{label}"%' for label in labels])
        
        query += " ORDER BY priority ASC, created_at ASC"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_task(row) for row in rows]
    
    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        task_type: Optional[str] = None,
        priority: Optional[int] = None,
        story_points: Optional[int] = None,
        estimated_minutes: Optional[int] = None,
        status: Optional[str] = None,
        parent_id: Optional[str] = None,
        acceptance_criteria: Optional[list[str]] = None,
        quality_score: Optional[float] = None,
        assignee: Optional[str] = None,
        labels: Optional[list[str]] = None,
        due_at: Optional[datetime] = None,
        defer_until: Optional[datetime] = None,
    ) -> Optional[Task]:
        """Update a task.
        
        Args:
            task_id: Task ID to update
            **kwargs: Fields to update
        
        Returns:
            Updated Task object or None if not found
        """
        # Build update query dynamically
        updates = []
        params: list[Any] = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if task_type is not None:
            updates.append("task_type = ?")
            params.append(task_type)
        
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)
        
        if story_points is not None:
            updates.append("story_points = ?")
            params.append(story_points)
        
        if estimated_minutes is not None:
            updates.append("estimated_minutes = ?")
            params.append(estimated_minutes)
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if parent_id is not None:
            updates.append("parent_id = ?")
            params.append(parent_id)
        
        if acceptance_criteria is not None:
            updates.append("acceptance_criteria = ?")
            params.append(json.dumps(acceptance_criteria))
        
        if quality_score is not None:
            updates.append("quality_score = ?")
            params.append(quality_score)
        
        if assignee is not None:
            updates.append("assignee = ?")
            params.append(assignee)
        
        if labels is not None:
            updates.append("labels = ?")
            params.append(json.dumps(labels))
        
        if due_at is not None:
            updates.append("due_at = ?")
            params.append(due_at.isoformat())
        
        if defer_until is not None:
            updates.append("defer_until = ?")
            params.append(defer_until.isoformat())
        
        if not updates:
            return self.get_task(task_id)
        
        # Always update updated_at
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        params.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        
        with self._connection() as conn:
            conn.execute(query, params)
            conn.commit()
        
        return self.get_task(task_id)
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task and its dependencies.
        
        Args:
            task_id: Task ID to delete
        
        Returns:
            True if deleted, False if not found
        """
        with self._connection() as conn:
            # Delete dependencies first
            conn.execute(
                "DELETE FROM dependencies WHERE task_id = ? OR depends_on_id = ?",
                (task_id, task_id)
            )
            
            # Delete the task
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_ready_tasks(self, limit: int = 10) -> list[Task]:
        """Get tasks that are ready to work on (no blockers).
        
        Args:
            limit: Maximum number of results
        
        Returns:
            List of ready tasks ordered by priority
        """
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT t.* FROM tasks t
                WHERE t.status = 'open'
                  AND (t.defer_until IS NULL OR t.defer_until <= datetime('now'))
                  AND NOT EXISTS (
                      SELECT 1 FROM dependencies d
                      JOIN tasks blocker ON d.depends_on_id = blocker.id
                      WHERE d.task_id = t.id
                        AND d.dep_type = 'blocks'
                        AND blocker.status NOT IN ('done', 'cancelled')
                  )
                ORDER BY t.priority ASC, t.created_at ASC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            
            return [self._row_to_task(row) for row in rows]
    
    def get_blocked_tasks(self) -> list[Task]:
        """Get tasks that are blocked by other tasks.
        
        Returns:
            List of blocked tasks
        """
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT t.* FROM tasks t
                JOIN dependencies d ON d.task_id = t.id
                JOIN tasks blocker ON d.depends_on_id = blocker.id
                WHERE d.dep_type = 'blocks'
                  AND blocker.status NOT IN ('done', 'cancelled')
                  AND t.status NOT IN ('done', 'cancelled')
                ORDER BY t.priority ASC, t.created_at ASC
                """
            ).fetchall()
            
            return [self._row_to_task(row) for row in rows]
    
    def get_children(self, parent_id: str) -> list[Task]:
        """Get child tasks of a parent.
        
        Args:
            parent_id: Parent task ID
        
        Returns:
            List of child tasks
        """
        return self.list_tasks(parent_id=parent_id)
    
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert a database row to a Task object."""
        data = dict(row)
        return Task.from_dict(data)
    
    # =========================================================================
    # Dependency Operations
    # =========================================================================
    
    def add_dependency(
        self,
        task_id: str,
        depends_on_id: str,
        dep_type: str = "blocks",
    ) -> Dependency:
        """Add a dependency between tasks.
        
        Args:
            task_id: The dependent task ID
            depends_on_id: The task it depends on
            dep_type: Type of dependency
        
        Returns:
            Created Dependency object
        """
        now = datetime.now()
        
        with self._connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO dependencies (task_id, depends_on_id, dep_type, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (task_id, depends_on_id, dep_type, now.isoformat())
            )
            conn.commit()
            
            return Dependency(
                id=cursor.lastrowid,
                task_id=task_id,
                depends_on_id=depends_on_id,
                dep_type=dep_type,
                created_at=now,
            )
    
    def remove_dependency(self, task_id: str, depends_on_id: str) -> bool:
        """Remove a dependency between tasks.
        
        Args:
            task_id: The dependent task ID
            depends_on_id: The task it depends on
        
        Returns:
            True if removed, False if not found
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM dependencies WHERE task_id = ? AND depends_on_id = ?",
                (task_id, depends_on_id)
            )
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_dependencies(self, task_id: str) -> list[Dependency]:
        """Get all dependencies for a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            List of dependencies
        """
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM dependencies WHERE task_id = ?",
                (task_id,)
            ).fetchall()
            
            return [Dependency.from_dict(dict(row)) for row in rows]
    
    def get_dependents(self, task_id: str) -> list[Dependency]:
        """Get tasks that depend on this task.
        
        Args:
            task_id: Task ID
        
        Returns:
            List of dependencies where this task is the blocker
        """
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM dependencies WHERE depends_on_id = ?",
                (task_id,)
            ).fetchall()
            
            return [Dependency.from_dict(dict(row)) for row in rows]
    
    # =========================================================================
    # Hook Operations
    # =========================================================================
    
    def add_hook(self, event: str, command: str) -> Hook:
        """Add a quality hook.
        
        Args:
            event: Event name (pre-close, post-create, etc.)
            command: Shell command to run
        
        Returns:
            Created Hook object
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO hooks (event, command, enabled) VALUES (?, ?, 1)",
                (event, command)
            )
            conn.commit()
            
            return Hook(
                id=cursor.lastrowid,
                event=event,
                command=command,
                enabled=True,
            )
    
    def remove_hook(self, hook_id: int) -> bool:
        """Remove a hook by ID.
        
        Args:
            hook_id: Hook ID
        
        Returns:
            True if removed, False if not found
        """
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM hooks WHERE id = ?", (hook_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def get_hooks(self, event: Optional[str] = None) -> list[Hook]:
        """Get hooks, optionally filtered by event.
        
        Args:
            event: Event name to filter by
        
        Returns:
            List of hooks
        """
        with self._connection() as conn:
            if event:
                rows = conn.execute(
                    "SELECT * FROM hooks WHERE event = ? AND enabled = 1",
                    (event,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM hooks").fetchall()
            
            return [Hook.from_dict(dict(row)) for row in rows]
    
    def set_hook_enabled(self, hook_id: int, enabled: bool) -> bool:
        """Enable or disable a hook.
        
        Args:
            hook_id: Hook ID
            enabled: Whether the hook should be enabled
        
        Returns:
            True if updated, False if not found
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "UPDATE hooks SET enabled = ? WHERE id = ?",
                (1 if enabled else 0, hook_id)
            )
            conn.commit()
            
            return cursor.rowcount > 0
    
    # =========================================================================
    # Config Operations
    # =========================================================================
    
    def get_config(self, key: str) -> Optional[str]:
        """Get a configuration value.
        
        Args:
            key: Config key
        
        Returns:
            Config value or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT value FROM config WHERE key = ?",
                (key,)
            ).fetchone()
            
            return row["value"] if row else None
    
    def set_config(self, key: str, value: str):
        """Set a configuration value.
        
        Args:
            key: Config key
            value: Config value
        """
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO config (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value)
            )
            conn.commit()
    
    def get_all_config(self) -> dict[str, str]:
        """Get all configuration values.
        
        Returns:
            Dictionary of config key-value pairs
        """
        with self._connection() as conn:
            rows = conn.execute("SELECT key, value FROM config").fetchall()
            return {row["key"]: row["value"] for row in rows}


def init_project(project_path: Path) -> Storage:
    """Initialize a new Chisel project.
    
    Args:
        project_path: Path to the project root
    
    Returns:
        Storage instance for the project
    """
    chisel_dir = project_path / ".chisel"
    chisel_dir.mkdir(exist_ok=True)
    
    db_path = chisel_dir / "chisel.db"
    storage = Storage(db_path)
    
    # Set default config
    storage.set_config("project_name", project_path.name)
    storage.set_config("id_prefix", "ch")
    storage.set_config("default_priority", "2")
    
    return storage


def get_storage(project_path: Optional[Path] = None) -> Optional[Storage]:
    """Get storage for a project, auto-discovering if needed.
    
    Args:
        project_path: Explicit project path, or None to auto-discover
    
    Returns:
        Storage instance or None if not in a project
    """
    from chisel.utils import find_chisel_root
    
    if project_path:
        db_path = project_path / ".chisel" / "chisel.db"
        if db_path.exists():
            return Storage(db_path)
        return None
    
    root = find_chisel_root()
    if root:
        return Storage(root / ".chisel" / "chisel.db")
    
    return None
