"""Tests for hooks module."""

import tempfile
from pathlib import Path

import pytest

from chisel.hooks import (
    get_hook_template,
    list_hook_templates,
    run_hook,
    run_hooks,
    validate_task,
)
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
        yield init_project(project_path), project_path


class TestRunHook:
    """Test running individual hooks."""
    
    def test_successful_hook(self):
        """Test running a successful hook."""
        result = run_hook("echo hello")
        
        assert result["success"] is True
        assert result["return_code"] == 0
        assert "hello" in result["stdout"]
    
    def test_failing_hook(self):
        """Test running a failing hook."""
        result = run_hook("exit 1")
        
        assert result["success"] is False
        assert result["return_code"] == 1
    
    def test_hook_with_task_id(self):
        """Test that task ID is passed as environment variable."""
        result = run_hook("echo $CHISEL_TASK_ID", task_id="ch-123abc")
        
        assert result["success"] is True
        assert "ch-123abc" in result["stdout"]
    
    def test_hook_timeout(self):
        """Test hook timeout."""
        result = run_hook("sleep 5", timeout=1)
        
        assert result["success"] is False
        assert "timed out" in result["stderr"]
    
    def test_hook_with_working_dir(self):
        """Test hook with working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_hook("pwd", working_dir=tmpdir)
            
            assert result["success"] is True
            assert tmpdir in result["stdout"]


class TestRunHooks:
    """Test running multiple hooks."""
    
    def test_run_hooks_for_event(self, storage):
        """Test running all hooks for an event."""
        storage.add_hook("pre-close", "echo hook1")
        storage.add_hook("pre-close", "echo hook2")
        storage.add_hook("post-create", "echo other")
        
        results = run_hooks(storage, "pre-close")
        
        assert len(results) == 2
        assert all(r["success"] for r in results)
    
    def test_run_hooks_empty(self, storage):
        """Test running hooks when none configured."""
        results = run_hooks(storage, "pre-close")
        
        assert results == []
    
    def test_run_hooks_with_task_id(self, storage):
        """Test running hooks with task ID."""
        storage.add_hook("pre-close", "echo $CHISEL_TASK_ID")
        
        results = run_hooks(storage, "pre-close", task_id="ch-test")
        
        assert len(results) == 1
        assert "ch-test" in results[0]["stdout"]


class TestValidateTask:
    """Test task validation."""
    
    def test_validate_passing(self, storage):
        """Test validation with passing hooks."""
        task = storage.create_task(title="Test task")
        storage.add_hook("pre-close", "echo passing")
        
        result = validate_task(storage, task.id)
        
        assert result["valid"] is True
        assert result["quality_score"] == 1.0
    
    def test_validate_failing(self, storage):
        """Test validation with failing hooks."""
        task = storage.create_task(title="Test task")
        storage.add_hook("pre-close", "exit 1")
        
        result = validate_task(storage, task.id)
        
        assert result["valid"] is False
        assert result["quality_score"] == 0.0
    
    def test_validate_partial(self, storage):
        """Test validation with some passing, some failing."""
        task = storage.create_task(title="Test task")
        storage.add_hook("pre-close", "echo pass")
        storage.add_hook("pre-close", "exit 1")
        
        result = validate_task(storage, task.id)
        
        assert result["valid"] is False
        assert result["quality_score"] == 0.5
    
    def test_validate_nonexistent_task(self, storage):
        """Test validation of nonexistent task."""
        result = validate_task(storage, "nonexistent")
        
        assert result["valid"] is False
        assert "not found" in result["error"]
    
    def test_validate_no_hooks(self, storage):
        """Test validation with no hooks configured."""
        task = storage.create_task(title="Test task")
        
        result = validate_task(storage, task.id)
        
        assert result["valid"] is True
        assert result["quality_score"] is None


class TestHookTemplates:
    """Test hook templates."""
    
    def test_get_template(self):
        """Test getting a hook template."""
        template = get_hook_template("pytest")
        
        assert template == "pytest tests/ -q"
    
    def test_get_nonexistent_template(self):
        """Test getting nonexistent template."""
        template = get_hook_template("nonexistent")
        
        assert template is None
    
    def test_list_templates(self):
        """Test listing all templates."""
        templates = list_hook_templates()
        
        assert "pytest" in templates
        assert "ruff" in templates
        assert "mypy" in templates
