"""Tests for models module."""

import json
from datetime import datetime

import pytest

from chisel.models import (
    Dependency,
    DependencyType,
    Hook,
    Priority,
    Task,
    TaskStatus,
    TaskType,
)


class TestTaskModel:
    """Test Task model."""
    
    def test_task_creation_defaults(self):
        """Test task creation with default values."""
        task = Task(
            id="ch-test123",
            title="Test task",
        )
        
        assert task.id == "ch-test123"
        assert task.title == "Test task"
        assert task.description == ""
        assert task.task_type == "task"
        assert task.priority == 2
        assert task.status == "open"
        assert task.parent_id is None
        assert task.acceptance_criteria == []
        assert task.labels == []
    
    def test_task_creation_full(self):
        """Test task creation with all fields."""
        now = datetime.now()
        task = Task(
            id="ch-full123",
            title="Full task",
            description="A full description",
            task_type="epic",
            priority=0,
            story_points=13,
            estimated_minutes=480,
            status="in_progress",
            parent_id="ch-parent",
            acceptance_criteria=["AC1", "AC2"],
            quality_score=0.85,
            assignee="developer",
            labels=["urgent", "backend"],
            created_at=now,
            updated_at=now,
            due_at=now,
            defer_until=now,
        )
        
        assert task.task_type == "epic"
        assert task.priority == 0
        assert task.story_points == 13
        assert task.estimated_minutes == 480
        assert task.quality_score == 0.85
        assert task.assignee == "developer"
        assert len(task.labels) == 2
        assert len(task.acceptance_criteria) == 2
    
    def test_task_to_dict(self):
        """Test task serialization to dict."""
        now = datetime.now()
        task = Task(
            id="ch-dict123",
            title="Dict task",
            description="Description",
            created_at=now,
            updated_at=now,
            labels=["test"],
            acceptance_criteria=["criteria1"],
        )
        
        data = task.to_dict()
        
        assert data["id"] == "ch-dict123"
        assert data["title"] == "Dict task"
        assert data["description"] == "Description"
        assert data["labels"] == ["test"]
        assert data["acceptance_criteria"] == ["criteria1"]
        assert data["created_at"] == now.isoformat()
    
    def test_task_to_dict_none_datetimes(self):
        """Test task serialization with None datetimes."""
        task = Task(
            id="ch-none",
            title="None dates",
        )
        
        data = task.to_dict()
        
        assert data["created_at"] is None
        assert data["due_at"] is None
        assert data["defer_until"] is None
    
    def test_task_from_dict(self):
        """Test task creation from dict."""
        data = {
            "id": "ch-fromdict",
            "title": "From dict",
            "description": "Test description",
            "task_type": "bug",
            "priority": 1,
            "status": "open",
            "labels": ["bug", "fix"],
            "acceptance_criteria": ["Fixed", "Tested"],
            "created_at": "2024-01-15T10:30:00",
            "updated_at": "2024-01-15T10:30:00",
        }
        
        task = Task.from_dict(data)
        
        assert task.id == "ch-fromdict"
        assert task.title == "From dict"
        assert task.task_type == "bug"
        assert task.priority == 1
        assert task.labels == ["bug", "fix"]
        assert isinstance(task.created_at, datetime)
    
    def test_task_from_dict_json_strings(self):
        """Test task from dict with JSON string fields."""
        data = {
            "id": "ch-json",
            "title": "JSON strings",
            "labels": '["label1", "label2"]',
            "acceptance_criteria": '["AC1", "AC2"]',
        }
        
        task = Task.from_dict(data)
        
        assert task.labels == ["label1", "label2"]
        assert task.acceptance_criteria == ["AC1", "AC2"]
    
    def test_task_from_dict_empty_json_strings(self):
        """Test task from dict with empty JSON string fields."""
        data = {
            "id": "ch-empty",
            "title": "Empty strings",
            "labels": "",
            "acceptance_criteria": "",
        }
        
        task = Task.from_dict(data)
        
        assert task.labels == []
        assert task.acceptance_criteria == []
    
    def test_task_roundtrip(self):
        """Test task serialization roundtrip."""
        now = datetime.now()
        original = Task(
            id="ch-roundtrip",
            title="Roundtrip",
            description="Test roundtrip",
            task_type="spike",
            priority=3,
            story_points=5,
            status="review",
            labels=["test", "roundtrip"],
            acceptance_criteria=["Passes tests"],
            created_at=now,
            updated_at=now,
        )
        
        data = original.to_dict()
        restored = Task.from_dict(data)
        
        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.task_type == original.task_type
        assert restored.labels == original.labels
        assert restored.acceptance_criteria == original.acceptance_criteria


class TestDependencyModel:
    """Test Dependency model."""
    
    def test_dependency_creation(self):
        """Test dependency creation."""
        dep = Dependency(
            id=1,
            task_id="ch-task",
            depends_on_id="ch-blocker",
            dep_type="blocks",
        )
        
        assert dep.id == 1
        assert dep.task_id == "ch-task"
        assert dep.depends_on_id == "ch-blocker"
        assert dep.dep_type == "blocks"
    
    def test_dependency_to_dict(self):
        """Test dependency serialization."""
        now = datetime.now()
        dep = Dependency(
            id=1,
            task_id="ch-task",
            depends_on_id="ch-blocker",
            dep_type="blocks",
            created_at=now,
        )
        
        data = dep.to_dict()
        
        assert data["id"] == 1
        assert data["task_id"] == "ch-task"
        assert data["depends_on_id"] == "ch-blocker"
        assert data["created_at"] == now.isoformat()
    
    def test_dependency_from_dict(self):
        """Test dependency from dict."""
        data = {
            "id": 5,
            "task_id": "ch-a",
            "depends_on_id": "ch-b",
            "dep_type": "related",
            "created_at": "2024-01-15T12:00:00",
        }
        
        dep = Dependency.from_dict(data)
        
        assert dep.id == 5
        assert dep.task_id == "ch-a"
        assert dep.dep_type == "related"
        assert isinstance(dep.created_at, datetime)


class TestHookModel:
    """Test Hook model."""
    
    def test_hook_creation(self):
        """Test hook creation."""
        hook = Hook(
            id=1,
            event="pre-close",
            command="pytest tests/",
            enabled=True,
        )
        
        assert hook.id == 1
        assert hook.event == "pre-close"
        assert hook.command == "pytest tests/"
        assert hook.enabled is True
    
    def test_hook_to_dict(self):
        """Test hook serialization."""
        hook = Hook(
            id=2,
            event="post-create",
            command="echo created",
            enabled=False,
        )
        
        data = hook.to_dict()
        
        assert data["id"] == 2
        assert data["event"] == "post-create"
        assert data["command"] == "echo created"
        assert data["enabled"] is False
    
    def test_hook_from_dict(self):
        """Test hook from dict."""
        data = {
            "id": 3,
            "event": "pre-close",
            "command": "ruff check .",
            "enabled": 1,  # SQLite stores as integer
        }
        
        hook = Hook.from_dict(data)
        
        assert hook.id == 3
        assert hook.enabled is True
    
    def test_hook_from_dict_disabled(self):
        """Test hook from dict with disabled flag."""
        data = {
            "id": 4,
            "event": "pre-close",
            "command": "test",
            "enabled": 0,
        }
        
        hook = Hook.from_dict(data)
        
        assert hook.enabled is False


class TestEnums:
    """Test enum definitions."""
    
    def test_dependency_types(self):
        """Test dependency type enum values."""
        assert DependencyType.BLOCKS.value == "blocks"
        assert DependencyType.PARENT_CHILD.value == "parent"
        assert DependencyType.RELATED.value == "related"
        assert DependencyType.DISCOVERED.value == "discovered"
    
    def test_task_statuses(self):
        """Test task status enum values."""
        assert TaskStatus.OPEN.value == "open"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.REVIEW.value == "review"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.CANCELLED.value == "cancelled"
    
    def test_task_types(self):
        """Test task type enum values."""
        assert TaskType.TASK.value == "task"
        assert TaskType.EPIC.value == "epic"
        assert TaskType.BUG.value == "bug"
        assert TaskType.SPIKE.value == "spike"
        assert TaskType.CHORE.value == "chore"
    
    def test_priority_levels(self):
        """Test priority enum values."""
        assert Priority.CRITICAL.value == 0
        assert Priority.HIGH.value == 1
        assert Priority.MEDIUM.value == 2
        assert Priority.LOW.value == 3
        assert Priority.BACKLOG.value == 4
