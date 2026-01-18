"""Tests for CLI module."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from chisel.cli import main
from chisel.storage import init_project


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        init_project(project_path)
        yield project_path


@pytest.fixture
def runner_with_project(runner, project_dir):
    """Create a CLI runner with an initialized project."""
    def run(*args, **kwargs):
        return runner.invoke(main, ["--project", str(project_dir)] + list(args), **kwargs)
    return run


class TestInit:
    """Test init command."""
    
    def test_init_creates_project(self, runner):
        """Test that init creates .chisel directory."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["init", "--json"])
            
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "project_root" in data
            assert Path(".chisel/chisel.db").exists()
    
    def test_init_fails_if_exists(self, runner, project_dir):
        """Test that init fails if project already exists."""
        result = runner.invoke(main, ["--project", str(project_dir), "init", "--json"])
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class TestCreate:
    """Test create command."""
    
    def test_create_task(self, runner_with_project):
        """Test creating a task."""
        result = runner_with_project("create", "Test task", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["title"] == "Test task"
        assert data["task"]["status"] == "open"
    
    def test_create_with_options(self, runner_with_project):
        """Test creating a task with options."""
        result = runner_with_project(
            "create", "Bug fix",
            "-t", "bug",
            "-p", "1",
            "-d", "Fix the login bug",
            "--points", "3",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["title"] == "Bug fix"
        assert data["task"]["task_type"] == "bug"
        assert data["task"]["priority"] == 1
        assert data["task"]["description"] == "Fix the login bug"
        assert data["task"]["story_points"] == 3
    
    def test_create_with_parent(self, runner_with_project):
        """Test creating a subtask."""
        # Create parent first
        result1 = runner_with_project("create", "Epic", "-t", "epic", "--json")
        parent_id = json.loads(result1.output)["task"]["id"]
        
        # Create child
        result2 = runner_with_project("create", "Subtask", "--parent", parent_id, "--json")
        
        assert result2.exit_code == 0
        data = json.loads(result2.output)
        assert data["task"]["parent_id"] == parent_id


class TestList:
    """Test list command."""
    
    def test_list_empty(self, runner_with_project):
        """Test listing tasks when none exist."""
        result = runner_with_project("list", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["tasks"] == []
    
    def test_list_tasks(self, runner_with_project):
        """Test listing tasks."""
        runner_with_project("create", "Task 1", "--json")
        runner_with_project("create", "Task 2", "--json")
        
        result = runner_with_project("list", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 2
    
    def test_list_with_status_filter(self, runner_with_project):
        """Test listing tasks with status filter."""
        result1 = runner_with_project("create", "Open task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        runner_with_project("update", task_id, "--status", "done", "--json")
        runner_with_project("create", "Another open", "--json")
        
        result = runner_with_project("list", "--status", "open", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["title"] == "Another open"


class TestShow:
    """Test show command."""
    
    def test_show_task(self, runner_with_project):
        """Test showing task details."""
        result1 = runner_with_project("create", "Test task", "-d", "Description", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project("show", task_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["id"] == task_id
        assert data["task"]["title"] == "Test task"
        assert data["task"]["description"] == "Description"
    
    def test_show_nonexistent(self, runner_with_project):
        """Test showing nonexistent task."""
        result = runner_with_project("show", "nonexistent", "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class TestUpdate:
    """Test update command."""
    
    def test_update_task(self, runner_with_project):
        """Test updating a task."""
        result1 = runner_with_project("create", "Original", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "update", task_id,
            "--title", "Updated",
            "--status", "in_progress",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["title"] == "Updated"
        assert data["task"]["status"] == "in_progress"


class TestCloseReopen:
    """Test close and reopen commands."""
    
    def test_close_task(self, runner_with_project):
        """Test closing a task."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project("close", task_id, "--reason", "Done", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["status"] == "done"
    
    def test_reopen_task(self, runner_with_project):
        """Test reopening a task."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        runner_with_project("close", task_id, "--json")
        
        result = runner_with_project("reopen", task_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["status"] == "open"


class TestReady:
    """Test ready command."""
    
    def test_ready_tasks(self, runner_with_project):
        """Test getting ready tasks."""
        runner_with_project("create", "Task 1", "--json")
        runner_with_project("create", "Task 2", "--json")
        
        result = runner_with_project("ready", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 2
    
    def test_ready_excludes_blocked(self, runner_with_project):
        """Test that ready excludes blocked tasks."""
        result1 = runner_with_project("create", "Blocker", "--json")
        blocker_id = json.loads(result1.output)["task"]["id"]
        
        result2 = runner_with_project("create", "Blocked", "--json")
        blocked_id = json.loads(result2.output)["task"]["id"]
        
        runner_with_project("dep", "add", blocked_id, "--blocked-by", blocker_id, "--json")
        
        result = runner_with_project("ready", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == blocker_id


class TestDependencies:
    """Test dependency commands."""
    
    def test_add_dependency(self, runner_with_project):
        """Test adding a dependency."""
        result1 = runner_with_project("create", "Task 1", "--json")
        t1_id = json.loads(result1.output)["task"]["id"]
        
        result2 = runner_with_project("create", "Task 2", "--json")
        t2_id = json.loads(result2.output)["task"]["id"]
        
        result = runner_with_project("dep", "add", t2_id, "--blocked-by", t1_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dependency"]["task_id"] == t2_id
        assert data["dependency"]["depends_on_id"] == t1_id
    
    def test_remove_dependency(self, runner_with_project):
        """Test removing a dependency."""
        result1 = runner_with_project("create", "Task 1", "--json")
        t1_id = json.loads(result1.output)["task"]["id"]
        
        result2 = runner_with_project("create", "Task 2", "--json")
        t2_id = json.loads(result2.output)["task"]["id"]
        
        runner_with_project("dep", "add", t2_id, "--blocked-by", t1_id, "--json")
        result = runner_with_project("dep", "remove", t2_id, t1_id, "--json")
        
        assert result.exit_code == 0
    
    def test_list_dependencies(self, runner_with_project):
        """Test listing dependencies."""
        result1 = runner_with_project("create", "Blocker", "--json")
        blocker_id = json.loads(result1.output)["task"]["id"]
        
        result2 = runner_with_project("create", "Blocked", "--json")
        blocked_id = json.loads(result2.output)["task"]["id"]
        
        runner_with_project("dep", "add", blocked_id, "--blocked-by", blocker_id, "--json")
        
        result = runner_with_project("dep", "list", blocked_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["blocked_by"]) == 1
        assert data["blocked_by"][0]["depends_on_id"] == blocker_id


class TestDecompose:
    """Test decompose command."""
    
    def test_decompose_task(self, runner_with_project):
        """Test decomposing a task."""
        result1 = runner_with_project("create", "Epic", "-t", "epic", "--json")
        epic_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "decompose", epic_id,
            "Subtask 1", "Subtask 2", "Subtask 3",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["subtasks"]) == 3
        assert all(s["parent_id"] == epic_id for s in data["subtasks"])
    
    def test_decompose_with_points(self, runner_with_project):
        """Test decomposing with story points."""
        result1 = runner_with_project("create", "Epic", "--json")
        epic_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "decompose", epic_id,
            "Sub 1", "Sub 2",
            "--points", "3,5",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["subtasks"][0]["story_points"] == 3
        assert data["subtasks"][1]["story_points"] == 5


class TestTree:
    """Test tree command."""
    
    def test_tree_view(self, runner_with_project):
        """Test tree view of task hierarchy."""
        result1 = runner_with_project("create", "Epic", "-t", "epic", "--json")
        epic_id = json.loads(result1.output)["task"]["id"]
        
        runner_with_project("decompose", epic_id, "Sub 1", "Sub 2", "--json")
        
        result = runner_with_project("tree", epic_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["tree"]["task"]["id"] == epic_id
        assert len(data["tree"]["children"]) == 2


class TestHooks:
    """Test hook commands."""
    
    def test_set_hook(self, runner_with_project):
        """Test setting a hook."""
        result = runner_with_project("hook", "set", "pre-close", "echo test", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["hook"]["event"] == "pre-close"
        assert data["hook"]["command"] == "echo test"
    
    def test_list_hooks(self, runner_with_project):
        """Test listing hooks."""
        runner_with_project("hook", "set", "pre-close", "echo 1", "--json")
        runner_with_project("hook", "set", "post-create", "echo 2", "--json")
        
        result = runner_with_project("hook", "list", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["hooks"]) == 2
    
    def test_remove_hook(self, runner_with_project):
        """Test removing a hook."""
        result1 = runner_with_project("hook", "set", "pre-close", "echo test", "--json")
        hook_id = json.loads(result1.output)["hook"]["id"]
        
        result = runner_with_project("hook", "remove", str(hook_id), "--json")
        
        assert result.exit_code == 0


class TestValidate:
    """Test validate command."""
    
    def test_validate_with_passing_hook(self, runner_with_project):
        """Test validation with passing hook."""
        runner_with_project("hook", "set", "pre-close", "echo passing", "--json")
        
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project("validate", task_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["valid"] is True
    
    def test_validate_with_failing_hook(self, runner_with_project):
        """Test validation with failing hook."""
        runner_with_project("hook", "set", "pre-close", "exit 1", "--json")
        
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project("validate", task_id, "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["valid"] is False
    
    def test_validate_nonexistent_task(self, runner_with_project):
        """Test validation of nonexistent task."""
        result = runner_with_project("validate", "nonexistent", "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class TestInfo:
    """Test info command."""
    
    def test_info_shows_project(self, runner_with_project):
        """Test info shows project information."""
        result = runner_with_project("info", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "project_root" in data
        assert "database" in data
        assert "config" in data


class TestBlocked:
    """Test blocked command."""
    
    def test_blocked_shows_blocked_tasks(self, runner_with_project):
        """Test blocked shows blocked tasks."""
        result1 = runner_with_project("create", "Blocker", "--json")
        blocker_id = json.loads(result1.output)["task"]["id"]
        
        result2 = runner_with_project("create", "Blocked", "--json")
        blocked_id = json.loads(result2.output)["task"]["id"]
        
        runner_with_project("dep", "add", blocked_id, "--blocked-by", blocker_id, "--json")
        
        result = runner_with_project("blocked", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == blocked_id
        assert len(data["tasks"][0]["blocked_by"]) == 1
    
    def test_blocked_empty_when_none_blocked(self, runner_with_project):
        """Test blocked returns empty when no blocked tasks."""
        runner_with_project("create", "Task 1", "--json")
        runner_with_project("create", "Task 2", "--json")
        
        result = runner_with_project("blocked", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 0


class TestCreateEdgeCases:
    """Test create command edge cases."""
    
    def test_create_with_labels(self, runner_with_project):
        """Test creating task with labels."""
        result = runner_with_project(
            "create", "Labeled task",
            "--labels", "bug,urgent,backend",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["labels"] == ["bug", "urgent", "backend"]
    
    def test_create_with_acceptance_criteria(self, runner_with_project):
        """Test creating task with acceptance criteria."""
        result = runner_with_project(
            "create", "Task with AC",
            "--criteria", "Tests pass",
            "--criteria", "Code reviewed",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["acceptance_criteria"] == ["Tests pass", "Code reviewed"]
    
    def test_create_with_estimate(self, runner_with_project):
        """Test creating task with time estimate."""
        result = runner_with_project(
            "create", "Estimated task",
            "--estimate", "120",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["estimated_minutes"] == 120
    
    def test_create_with_assignee(self, runner_with_project):
        """Test creating task with assignee."""
        result = runner_with_project(
            "create", "Assigned task",
            "--assignee", "developer@example.com",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["assignee"] == "developer@example.com"


class TestUpdateEdgeCases:
    """Test update command edge cases."""
    
    def test_update_nonexistent_task(self, runner_with_project):
        """Test updating nonexistent task."""
        result = runner_with_project(
            "update", "nonexistent",
            "--title", "New title",
            "--json"
        )
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_update_priority(self, runner_with_project):
        """Test updating task priority."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "update", task_id,
            "--priority", "0",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["priority"] == 0
    
    def test_update_labels(self, runner_with_project):
        """Test updating task labels."""
        result1 = runner_with_project(
            "create", "Task",
            "--labels", "old",
            "--json"
        )
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "update", task_id,
            "--labels", "new,updated",
            "--json"
        )
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["labels"] == ["new", "updated"]


class TestReopenEdgeCases:
    """Test reopen command edge cases."""
    
    def test_reopen_nonexistent_task(self, runner_with_project):
        """Test reopening nonexistent task."""
        result = runner_with_project("reopen", "nonexistent", "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_reopen_open_task(self, runner_with_project):
        """Test reopening already open task."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project("reopen", task_id, "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_reopen_cancelled_task(self, runner_with_project):
        """Test reopening cancelled task."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        runner_with_project("update", task_id, "--status", "cancelled", "--json")
        
        result = runner_with_project("reopen", task_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["status"] == "open"


class TestDependencyEdgeCases:
    """Test dependency command edge cases."""
    
    def test_dep_add_self_dependency(self, runner_with_project):
        """Test adding self-dependency fails."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "dep", "add", task_id,
            "--blocked-by", task_id,
            "--json"
        )
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_dep_add_nonexistent_task(self, runner_with_project):
        """Test adding dependency with nonexistent task."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "dep", "add", task_id,
            "--blocked-by", "nonexistent",
            "--json"
        )
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_dep_add_nonexistent_blocked_task(self, runner_with_project):
        """Test adding dependency with nonexistent blocked task."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "dep", "add", "nonexistent",
            "--blocked-by", task_id,
            "--json"
        )
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_dep_remove_nonexistent(self, runner_with_project):
        """Test removing nonexistent dependency."""
        result1 = runner_with_project("create", "Task 1", "--json")
        t1_id = json.loads(result1.output)["task"]["id"]
        
        result2 = runner_with_project("create", "Task 2", "--json")
        t2_id = json.loads(result2.output)["task"]["id"]
        
        result = runner_with_project("dep", "remove", t2_id, t1_id, "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_dep_list_nonexistent_task(self, runner_with_project):
        """Test listing dependencies for nonexistent task."""
        result = runner_with_project("dep", "list", "nonexistent", "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class TestDecomposeEdgeCases:
    """Test decompose command edge cases."""
    
    def test_decompose_nonexistent_task(self, runner_with_project):
        """Test decomposing nonexistent task."""
        result = runner_with_project(
            "decompose", "nonexistent",
            "Sub 1", "Sub 2",
            "--json"
        )
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_decompose_mismatched_points(self, runner_with_project):
        """Test decompose with mismatched points count."""
        result1 = runner_with_project("create", "Epic", "--json")
        epic_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "decompose", epic_id,
            "Sub 1", "Sub 2", "Sub 3",
            "--points", "3,5",  # Only 2 points for 3 subtasks
            "--json"
        )
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_decompose_invalid_points(self, runner_with_project):
        """Test decompose with invalid points format."""
        result1 = runner_with_project("create", "Epic", "--json")
        epic_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project(
            "decompose", epic_id,
            "Sub 1",
            "--points", "invalid",
            "--json"
        )
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class TestTreeEdgeCases:
    """Test tree command edge cases."""
    
    def test_tree_nonexistent_task(self, runner_with_project):
        """Test tree for nonexistent task."""
        result = runner_with_project("tree", "nonexistent", "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_tree_nested_hierarchy(self, runner_with_project):
        """Test tree with deeply nested hierarchy."""
        result1 = runner_with_project("create", "Grandparent", "-t", "epic", "--json")
        grandparent_id = json.loads(result1.output)["task"]["id"]
        
        result2 = runner_with_project(
            "create", "Parent",
            "--parent", grandparent_id,
            "--json"
        )
        parent_id = json.loads(result2.output)["task"]["id"]
        
        runner_with_project(
            "create", "Child",
            "--parent", parent_id,
            "--json"
        )
        
        result = runner_with_project("tree", grandparent_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tree"]["children"]) == 1
        assert len(data["tree"]["children"][0]["children"]) == 1


class TestCloseEdgeCases:
    """Test close command edge cases."""
    
    def test_close_nonexistent_task(self, runner_with_project):
        """Test closing nonexistent task."""
        result = runner_with_project("close", "nonexistent", "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data
    
    def test_close_without_reason(self, runner_with_project):
        """Test closing without reason."""
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project("close", task_id, "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["task"]["status"] == "done"
    
    def test_close_with_failing_hook(self, runner_with_project):
        """Test close fails when hook fails."""
        runner_with_project("hook", "set", "pre-close", "exit 1", "--json")
        
        result1 = runner_with_project("create", "Task", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project("close", task_id, "--json")
        
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "error" in data


class TestListEdgeCases:
    """Test list command edge cases."""
    
    def test_list_by_priority(self, runner_with_project):
        """Test listing by priority."""
        runner_with_project("create", "P0 task", "-p", "0", "--json")
        runner_with_project("create", "P1 task", "-p", "1", "--json")
        runner_with_project("create", "P2 task", "-p", "2", "--json")
        
        result = runner_with_project("list", "--priority", "0", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["priority"] == 0
    
    def test_list_by_type(self, runner_with_project):
        """Test listing by type."""
        runner_with_project("create", "Bug 1", "-t", "bug", "--json")
        runner_with_project("create", "Task 1", "-t", "task", "--json")
        runner_with_project("create", "Bug 2", "-t", "bug", "--json")
        
        result = runner_with_project("list", "--type", "bug", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 2
        assert all(t["task_type"] == "bug" for t in data["tasks"])
    
    def test_list_with_limit(self, runner_with_project):
        """Test listing with limit."""
        for i in range(10):
            runner_with_project("create", f"Task {i}", "--json")
        
        result = runner_with_project("list", "--limit", "3", "--json")
        
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["tasks"]) == 3


class TestHumanReadableOutput:
    """Test human-readable (non-JSON) output."""
    
    def test_list_human_readable(self, runner_with_project):
        """Test list with human-readable output."""
        runner_with_project("create", "Task 1", "--json")
        runner_with_project("create", "Task 2", "--json")
        
        result = runner_with_project("list")  # No --json
        
        assert result.exit_code == 0
        assert "Task 1" in result.output
        assert "Task 2" in result.output
        assert "Total: 2" in result.output
    
    def test_show_human_readable(self, runner_with_project):
        """Test show with human-readable output."""
        result1 = runner_with_project("create", "Test Task", "-d", "Description", "--json")
        task_id = json.loads(result1.output)["task"]["id"]
        
        result = runner_with_project("show", task_id)  # No --json
        
        assert result.exit_code == 0
        assert task_id in result.output
        assert "Test Task" in result.output
    
    def test_ready_human_readable(self, runner_with_project):
        """Test ready with human-readable output."""
        runner_with_project("create", "Ready Task", "--json")
        
        result = runner_with_project("ready")  # No --json
        
        assert result.exit_code == 0
        assert "Ready Task" in result.output


class TestHookListHumanReadable:
    """Test hook list human-readable output."""
    
    def test_hook_list_human_readable(self, runner_with_project):
        """Test hook list with human-readable output."""
        runner_with_project("hook", "set", "pre-close", "pytest", "--json")
        
        result = runner_with_project("hook", "list")  # No --json
        
        assert result.exit_code == 0
        assert "pre-close" in result.output
        assert "pytest" in result.output
    
    def test_hook_list_empty_human_readable(self, runner_with_project):
        """Test hook list when empty."""
        result = runner_with_project("hook", "list")  # No --json
        
        assert result.exit_code == 0
        assert "No hooks" in result.output
