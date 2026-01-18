"""Tests for storage module."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from chisel.storage import Storage, init_project


@pytest.fixture
def storage():
    """Create a temporary storage instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield Storage(db_path)


@pytest.fixture
def project_storage():
    """Create a storage instance via project init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        yield init_project(project_path)


class TestTaskCRUD:
    """Test task CRUD operations."""
    
    def test_create_task(self, storage):
        """Test creating a task."""
        task = storage.create_task(
            title="Test task",
            description="Test description",
            priority=1,
        )
        
        assert task.id.startswith("ch-")
        assert task.title == "Test task"
        assert task.description == "Test description"
        assert task.priority == 1
        assert task.status == "open"
        assert task.created_at is not None
    
    def test_get_task(self, storage):
        """Test retrieving a task."""
        created = storage.create_task(title="Test task")
        retrieved = storage.get_task(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == created.title
    
    def test_get_nonexistent_task(self, storage):
        """Test retrieving a nonexistent task."""
        task = storage.get_task("nonexistent")
        assert task is None
    
    def test_list_tasks(self, storage):
        """Test listing tasks."""
        storage.create_task(title="Task 1", priority=1)
        storage.create_task(title="Task 2", priority=2)
        storage.create_task(title="Task 3", priority=1)
        
        tasks = storage.list_tasks()
        assert len(tasks) == 3
        
        # Should be ordered by priority
        assert tasks[0].priority == 1
        assert tasks[1].priority == 1
        assert tasks[2].priority == 2
    
    def test_list_tasks_with_filters(self, storage):
        """Test listing tasks with filters."""
        storage.create_task(title="Open task")  # Default status is open
        t2 = storage.create_task(title="Done task")
        storage.update_task(t2.id, status="done")
        
        open_tasks = storage.list_tasks(status="open")
        assert len(open_tasks) == 1
        assert open_tasks[0].title == "Open task"
        
        done_tasks = storage.list_tasks(status="done")
        assert len(done_tasks) == 1
        assert done_tasks[0].title == "Done task"
    
    def test_update_task(self, storage):
        """Test updating a task."""
        task = storage.create_task(title="Original")
        
        updated = storage.update_task(
            task.id,
            title="Updated",
            priority=0,
            status="in_progress",
        )
        
        assert updated.title == "Updated"
        assert updated.priority == 0
        assert updated.status == "in_progress"
        assert updated.updated_at > task.updated_at
    
    def test_delete_task(self, storage):
        """Test deleting a task."""
        task = storage.create_task(title="To delete")
        
        result = storage.delete_task(task.id)
        assert result is True
        
        retrieved = storage.get_task(task.id)
        assert retrieved is None
    
    def test_delete_nonexistent_task(self, storage):
        """Test deleting a nonexistent task."""
        result = storage.delete_task("nonexistent")
        assert result is False


class TestReadyTasks:
    """Test ready task calculation."""
    
    def test_ready_tasks_no_blockers(self, storage):
        """Test getting ready tasks with no blockers."""
        storage.create_task(title="Task 1")
        storage.create_task(title="Task 2")
        
        ready = storage.get_ready_tasks()
        assert len(ready) == 2
    
    def test_ready_tasks_with_blockers(self, storage):
        """Test that blocked tasks are excluded."""
        t1 = storage.create_task(title="Blocker")
        t2 = storage.create_task(title="Blocked")
        
        storage.add_dependency(t2.id, t1.id, "blocks")
        
        ready = storage.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == t1.id
    
    def test_ready_tasks_blocker_done(self, storage):
        """Test that tasks become ready when blocker is done."""
        t1 = storage.create_task(title="Blocker")
        t2 = storage.create_task(title="Blocked")
        
        storage.add_dependency(t2.id, t1.id, "blocks")
        storage.update_task(t1.id, status="done")
        
        ready = storage.get_ready_tasks()
        assert len(ready) == 1
        assert ready[0].id == t2.id
    
    def test_ready_tasks_respects_limit(self, storage):
        """Test that ready tasks respects limit."""
        for i in range(5):
            storage.create_task(title=f"Task {i}")
        
        ready = storage.get_ready_tasks(limit=3)
        assert len(ready) == 3


class TestDependencies:
    """Test dependency operations."""
    
    def test_add_dependency(self, storage):
        """Test adding a dependency."""
        t1 = storage.create_task(title="Task 1")
        t2 = storage.create_task(title="Task 2")
        
        dep = storage.add_dependency(t2.id, t1.id, "blocks")
        
        assert dep.task_id == t2.id
        assert dep.depends_on_id == t1.id
        assert dep.dep_type == "blocks"
    
    def test_get_dependencies(self, storage):
        """Test getting dependencies for a task."""
        t1 = storage.create_task(title="Blocker 1")
        t2 = storage.create_task(title="Blocker 2")
        t3 = storage.create_task(title="Blocked")
        
        storage.add_dependency(t3.id, t1.id, "blocks")
        storage.add_dependency(t3.id, t2.id, "blocks")
        
        deps = storage.get_dependencies(t3.id)
        assert len(deps) == 2
    
    def test_get_dependents(self, storage):
        """Test getting tasks that depend on a task."""
        t1 = storage.create_task(title="Blocker")
        t2 = storage.create_task(title="Blocked 1")
        t3 = storage.create_task(title="Blocked 2")
        
        storage.add_dependency(t2.id, t1.id, "blocks")
        storage.add_dependency(t3.id, t1.id, "blocks")
        
        dependents = storage.get_dependents(t1.id)
        assert len(dependents) == 2
    
    def test_remove_dependency(self, storage):
        """Test removing a dependency."""
        t1 = storage.create_task(title="Task 1")
        t2 = storage.create_task(title="Task 2")
        
        storage.add_dependency(t2.id, t1.id, "blocks")
        
        result = storage.remove_dependency(t2.id, t1.id)
        assert result is True
        
        deps = storage.get_dependencies(t2.id)
        assert len(deps) == 0
    
    def test_blocked_tasks(self, storage):
        """Test getting blocked tasks."""
        t1 = storage.create_task(title="Blocker")
        t2 = storage.create_task(title="Blocked")
        t3 = storage.create_task(title="Not blocked")
        
        storage.add_dependency(t2.id, t1.id, "blocks")
        
        blocked = storage.get_blocked_tasks()
        assert len(blocked) == 1
        assert blocked[0].id == t2.id


class TestHierarchy:
    """Test parent-child hierarchy."""
    
    def test_create_child_task(self, storage):
        """Test creating a child task."""
        parent = storage.create_task(title="Parent", task_type="epic")
        child = storage.create_task(title="Child", parent_id=parent.id)
        
        assert child.parent_id == parent.id
    
    def test_get_children(self, storage):
        """Test getting child tasks."""
        parent = storage.create_task(title="Parent", task_type="epic")
        storage.create_task(title="Child 1", parent_id=parent.id)
        storage.create_task(title="Child 2", parent_id=parent.id)
        storage.create_task(title="Other task")
        
        children = storage.get_children(parent.id)
        assert len(children) == 2


class TestHooks:
    """Test hook operations."""
    
    def test_add_hook(self, storage):
        """Test adding a hook."""
        hook = storage.add_hook("pre-close", "pytest tests/ -q")
        
        assert hook.event == "pre-close"
        assert hook.command == "pytest tests/ -q"
        assert hook.enabled is True
    
    def test_get_hooks(self, storage):
        """Test getting hooks."""
        storage.add_hook("pre-close", "pytest tests/")
        storage.add_hook("pre-close", "ruff check .")
        storage.add_hook("post-create", "echo Created")
        
        all_hooks = storage.get_hooks()
        assert len(all_hooks) == 3
        
        pre_close = storage.get_hooks("pre-close")
        assert len(pre_close) == 2
    
    def test_remove_hook(self, storage):
        """Test removing a hook."""
        hook = storage.add_hook("pre-close", "test")
        
        result = storage.remove_hook(hook.id)
        assert result is True
        
        hooks = storage.get_hooks()
        assert len(hooks) == 0
    
    def test_enable_disable_hook(self, storage):
        """Test enabling/disabling a hook."""
        hook = storage.add_hook("pre-close", "test")
        
        storage.set_hook_enabled(hook.id, False)
        hooks = storage.get_hooks("pre-close")
        assert len(hooks) == 0  # Disabled hooks not returned by default


class TestConfig:
    """Test configuration operations."""
    
    def test_set_get_config(self, storage):
        """Test setting and getting config."""
        storage.set_config("test_key", "test_value")
        
        value = storage.get_config("test_key")
        assert value == "test_value"
    
    def test_get_nonexistent_config(self, storage):
        """Test getting nonexistent config."""
        value = storage.get_config("nonexistent")
        assert value is None
    
    def test_get_all_config(self, storage):
        """Test getting all config."""
        storage.set_config("key1", "value1")
        storage.set_config("key2", "value2")
        
        config = storage.get_all_config()
        assert config["key1"] == "value1"
        assert config["key2"] == "value2"
    
    def test_project_init_sets_defaults(self, project_storage):
        """Test that project init sets default config."""
        config = project_storage.get_all_config()
        
        assert "project_name" in config
        assert config["id_prefix"] == "ch"
        assert config["default_priority"] == "2"
    
    def test_config_update_existing(self, storage):
        """Test updating existing config value."""
        storage.set_config("key", "value1")
        storage.set_config("key", "value2")
        
        value = storage.get_config("key")
        assert value == "value2"


class TestTaskEdgeCases:
    """Test edge cases for task operations."""
    
    def test_create_task_with_all_fields(self, storage):
        """Test creating task with all possible fields."""
        from datetime import datetime
        
        now = datetime.now()
        task = storage.create_task(
            title="Full task",
            description="Full description",
            task_type="epic",
            priority=0,
            story_points=13,
            estimated_minutes=480,
            parent_id=None,
            acceptance_criteria=["AC1", "AC2", "AC3"],
            assignee="developer@example.com",
            labels=["urgent", "backend", "api"],
            due_at=now,
            defer_until=now,
            id_prefix="epic",
        )
        
        assert task.id.startswith("epic-")
        assert task.story_points == 13
        assert task.estimated_minutes == 480
        assert len(task.acceptance_criteria) == 3
        assert len(task.labels) == 3
        assert task.due_at is not None
    
    def test_update_task_no_changes(self, storage):
        """Test updating task with no changes."""
        task = storage.create_task(title="Original")
        
        updated = storage.update_task(task.id)
        
        assert updated.title == task.title
        assert updated.updated_at >= task.updated_at
    
    def test_update_nonexistent_task(self, storage):
        """Test updating nonexistent task returns None."""
        result = storage.update_task("nonexistent", title="New")
        
        # Should return None or the task if found
        # Based on implementation, it returns get_task result
        assert result is None
    
    def test_list_tasks_by_type(self, storage):
        """Test listing tasks by type."""
        storage.create_task(title="Bug 1", task_type="bug")
        storage.create_task(title="Task 1", task_type="task")
        storage.create_task(title="Bug 2", task_type="bug")
        
        bugs = storage.list_tasks(task_type="bug")
        
        assert len(bugs) == 2
        assert all(t.task_type == "bug" for t in bugs)
    
    def test_list_tasks_by_assignee(self, storage):
        """Test listing tasks by assignee."""
        storage.create_task(title="Alice task", assignee="alice")
        storage.create_task(title="Bob task", assignee="bob")
        storage.create_task(title="Alice task 2", assignee="alice")
        
        alice_tasks = storage.list_tasks(assignee="alice")
        
        assert len(alice_tasks) == 2
        assert all(t.assignee == "alice" for t in alice_tasks)
    
    def test_list_tasks_by_labels(self, storage):
        """Test listing tasks by labels."""
        storage.create_task(title="Task 1", labels=["urgent", "backend"])
        storage.create_task(title="Task 2", labels=["frontend"])
        storage.create_task(title="Task 3", labels=["urgent", "frontend"])
        
        urgent_tasks = storage.list_tasks(labels=["urgent"])
        
        assert len(urgent_tasks) == 2
    
    def test_list_tasks_with_limit(self, storage):
        """Test listing tasks with limit."""
        for i in range(10):
            storage.create_task(title=f"Task {i}")
        
        tasks = storage.list_tasks(limit=5)
        
        assert len(tasks) == 5
    
    def test_delete_task_removes_dependencies(self, storage):
        """Test deleting task also removes its dependencies."""
        t1 = storage.create_task(title="Task 1")
        t2 = storage.create_task(title="Task 2")
        t3 = storage.create_task(title="Task 3")
        
        storage.add_dependency(t2.id, t1.id, "blocks")
        storage.add_dependency(t3.id, t2.id, "blocks")
        
        storage.delete_task(t2.id)
        
        # t2's dependencies should be gone
        deps = storage.get_dependencies(t3.id)
        assert not any(d.depends_on_id == t2.id for d in deps)


class TestDependencyEdgeCases:
    """Test edge cases for dependency operations."""
    
    def test_duplicate_dependency(self, storage):
        """Test adding duplicate dependency raises error."""
        t1 = storage.create_task(title="Task 1")
        t2 = storage.create_task(title="Task 2")
        
        storage.add_dependency(t2.id, t1.id, "blocks")
        
        # Adding same dependency again should raise
        with pytest.raises(Exception):
            storage.add_dependency(t2.id, t1.id, "blocks")
    
    def test_remove_nonexistent_dependency(self, storage):
        """Test removing nonexistent dependency."""
        t1 = storage.create_task(title="Task 1")
        t2 = storage.create_task(title="Task 2")
        
        result = storage.remove_dependency(t2.id, t1.id)
        
        assert result is False
    
    def test_ready_tasks_excludes_done(self, storage):
        """Test ready tasks excludes done tasks."""
        t1 = storage.create_task(title="Open")
        t2 = storage.create_task(title="Done")
        storage.update_task(t2.id, status="done")
        
        ready = storage.get_ready_tasks()
        
        assert len(ready) == 1
        assert ready[0].id == t1.id
    
    def test_ready_tasks_excludes_in_progress(self, storage):
        """Test ready tasks only returns open tasks."""
        t1 = storage.create_task(title="Open")
        t2 = storage.create_task(title="In Progress")
        storage.update_task(t2.id, status="in_progress")
        
        ready = storage.get_ready_tasks()
        
        assert len(ready) == 1
        assert ready[0].id == t1.id
    
    def test_blocked_excludes_done_blockers(self, storage):
        """Test blocked tasks excludes tasks blocked by done tasks."""
        t1 = storage.create_task(title="Blocker")
        t2 = storage.create_task(title="Blocked")
        storage.add_dependency(t2.id, t1.id, "blocks")
        
        # Initially blocked
        blocked = storage.get_blocked_tasks()
        assert len(blocked) == 1
        
        # Complete blocker
        storage.update_task(t1.id, status="done")
        
        # No longer blocked
        blocked = storage.get_blocked_tasks()
        assert len(blocked) == 0
    
    def test_chain_of_dependencies(self, storage):
        """Test chain of dependencies (A -> B -> C)."""
        t1 = storage.create_task(title="First")
        t2 = storage.create_task(title="Second")
        t3 = storage.create_task(title="Third")
        
        storage.add_dependency(t2.id, t1.id, "blocks")
        storage.add_dependency(t3.id, t2.id, "blocks")
        
        ready = storage.get_ready_tasks()
        
        # Only t1 should be ready
        assert len(ready) == 1
        assert ready[0].id == t1.id


class TestHookEdgeCases:
    """Test edge cases for hook operations."""
    
    def test_remove_nonexistent_hook(self, storage):
        """Test removing nonexistent hook."""
        result = storage.remove_hook(999)
        
        assert result is False
    
    def test_set_hook_enabled_nonexistent(self, storage):
        """Test enabling nonexistent hook."""
        result = storage.set_hook_enabled(999, True)
        
        assert result is False
    
    def test_multiple_hooks_same_event(self, storage):
        """Test multiple hooks for same event."""
        storage.add_hook("pre-close", "echo 1")
        storage.add_hook("pre-close", "echo 2")
        storage.add_hook("pre-close", "echo 3")
        
        hooks = storage.get_hooks("pre-close")
        
        assert len(hooks) == 3


class TestStorageGetStorage:
    """Test get_storage function."""
    
    def test_get_storage_with_explicit_path(self):
        """Test get_storage with explicit project path."""
        from chisel.storage import get_storage, init_project
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            init_project(project_path)
            
            storage = get_storage(project_path)
            
            assert storage is not None
    
    def test_get_storage_nonexistent_path(self):
        """Test get_storage with nonexistent path."""
        from chisel.storage import get_storage
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = get_storage(Path(tmpdir))
            
            assert storage is None
