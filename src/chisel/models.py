"""Data models for Chisel task manager."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DependencyType(Enum):
    """Types of task dependencies."""
    BLOCKS = "blocks"           # A blocks B (B can't start until A done)
    PARENT_CHILD = "parent"     # Hierarchical decomposition
    RELATED = "related"         # Informational link
    DISCOVERED = "discovered"   # Found while working on another task


class TaskStatus(Enum):
    """Standard task statuses."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Standard task types."""
    TASK = "task"
    EPIC = "epic"
    BUG = "bug"
    SPIKE = "spike"
    CHORE = "chore"


class Priority(Enum):
    """Task priority levels."""
    CRITICAL = 0  # Drop everything
    HIGH = 1      # Do today
    MEDIUM = 2    # This week (default)
    LOW = 3       # When time permits
    BACKLOG = 4   # Someday


@dataclass
class Task:
    """Represents a task in the system."""
    id: str
    title: str
    description: str = ""
    
    # Classification
    task_type: str = "task"
    priority: int = 2  # 0=critical, 1=high, 2=medium, 3=low, 4=backlog
    
    # Estimation
    story_points: Optional[int] = None
    estimated_minutes: Optional[int] = None
    
    # Status
    status: str = "open"
    
    # Hierarchy
    parent_id: Optional[str] = None
    
    # Quality
    acceptance_criteria: list[str] = field(default_factory=list)
    quality_score: Optional[float] = None  # 0.0-1.0, set by hooks
    
    # Metadata
    assignee: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    defer_until: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "priority": self.priority,
            "story_points": self.story_points,
            "estimated_minutes": self.estimated_minutes,
            "status": self.status,
            "parent_id": self.parent_id,
            "acceptance_criteria": self.acceptance_criteria,
            "quality_score": self.quality_score,
            "assignee": self.assignee,
            "labels": self.labels,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "defer_until": self.defer_until.isoformat() if self.defer_until else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create a Task from a dictionary."""
        # Parse datetime fields
        for field_name in ["created_at", "updated_at", "due_at", "defer_until"]:
            if data.get(field_name) and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        # Parse list fields from JSON if needed
        if isinstance(data.get("acceptance_criteria"), str):
            import json
            data["acceptance_criteria"] = json.loads(data["acceptance_criteria"]) if data["acceptance_criteria"] else []
        if isinstance(data.get("labels"), str):
            import json
            data["labels"] = json.loads(data["labels"]) if data["labels"] else []
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Dependency:
    """Represents a dependency between tasks."""
    id: Optional[int]
    task_id: str           # The dependent task
    depends_on_id: str     # The task it depends on
    dep_type: str = "blocks"
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert dependency to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "depends_on_id": self.depends_on_id,
            "dep_type": self.dep_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Dependency":
        """Create a Dependency from a dictionary."""
        if data.get("created_at") and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Hook:
    """Represents a quality hook."""
    id: Optional[int]
    event: str             # pre-close, post-create, etc.
    command: str           # Shell command to run
    enabled: bool = True
    
    def to_dict(self) -> dict:
        """Convert hook to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "event": self.event,
            "command": self.command,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Hook":
        """Create a Hook from a dictionary."""
        if "enabled" in data:
            data["enabled"] = bool(data["enabled"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
