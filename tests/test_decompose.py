"""Tests for decompose module."""

import tempfile
from pathlib import Path

import pytest

from chisel.decompose import (
    decompose_task,
    get_subtask_progress,
    get_task_tree,
    suggest_decomposition,
    update_parent_status,
)
from chisel.models import Task
from chisel.storage import Storage


@pytest.fixture
def storage():
    """Create a temporary storage instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield Storage(db_path)


class TestDecomposeTask:
    """Test task decomposition."""
    
    def test_decompose_basic(self, storage):
        """Test basic task decomposition."""
        parent = storage.create_task(title="Parent task", task_type="epic")
        
        result = decompose_task(
            storage,
            parent.id,
            ["Subtask 1", "Subtask 2", "Subtask 3"],
        )
        
        assert "error" not in result
        assert len(result["subtasks"]) == 3
        assert all(s["parent_id"] == parent.id for s in result["subtasks"])
    
    def test_decompose_with_points(self, storage):
        """Test decomposition with story points."""
        parent = storage.create_task(title="Epic")
        
        result = decompose_task(
            storage,
            parent.id,
            ["Sub 1", "Sub 2", "Sub 3"],
            story_points=[2, 5, 3],
        )
        
        assert result["subtasks"][0]["story_points"] == 2
        assert result["subtasks"][1]["story_points"] == 5
        assert result["subtasks"][2]["story_points"] == 3
    
    def test_decompose_partial_points(self, storage):
        """Test decomposition with partial story points."""
        parent = storage.create_task(title="Epic")
        
        result = decompose_task(
            storage,
            parent.id,
            ["Sub 1", "Sub 2", "Sub 3"],
            story_points=[2],  # Only one point
        )
        
        assert result["subtasks"][0]["story_points"] == 2
        assert result["subtasks"][1]["story_points"] is None
        assert result["subtasks"][2]["story_points"] is None
    
    def test_decompose_inherits_priority(self, storage):
        """Test subtasks inherit parent priority."""
        parent = storage.create_task(title="High priority", priority=1)
        
        result = decompose_task(
            storage,
            parent.id,
            ["Sub 1", "Sub 2"],
        )
        
        assert result["subtasks"][0]["priority"] == 1
        assert result["subtasks"][1]["priority"] == 1
    
    def test_decompose_converts_to_epic(self, storage):
        """Test parent is converted to epic type."""
        parent = storage.create_task(title="Regular task", task_type="task")
        
        result = decompose_task(
            storage,
            parent.id,
            ["Sub 1"],
        )
        
        assert result["parent"]["task_type"] == "epic"
    
    def test_decompose_nonexistent_parent(self, storage):
        """Test decomposition with nonexistent parent."""
        result = decompose_task(
            storage,
            "nonexistent",
            ["Sub 1"],
        )
        
        assert "error" in result
        assert "not found" in result["error"]
    
    def test_decompose_empty_subtasks(self, storage):
        """Test decomposition with empty subtask list."""
        parent = storage.create_task(title="Parent")
        
        result = decompose_task(
            storage,
            parent.id,
            [],
        )
        
        assert len(result["subtasks"]) == 0


class TestGetTaskTree:
    """Test task tree retrieval."""
    
    def test_tree_single_task(self, storage):
        """Test tree with single task (no children)."""
        task = storage.create_task(title="Single task")
        
        result = get_task_tree(storage, task.id)
        
        assert "error" not in result
        assert result["tree"]["task"]["id"] == task.id
        assert result["tree"]["children"] == []
    
    def test_tree_with_children(self, storage):
        """Test tree with children."""
        parent = storage.create_task(title="Parent")
        storage.create_task(title="Child 1", parent_id=parent.id)
        storage.create_task(title="Child 2", parent_id=parent.id)
        
        result = get_task_tree(storage, parent.id)
        
        assert len(result["tree"]["children"]) == 2
    
    def test_tree_nested(self, storage):
        """Test deeply nested tree."""
        grandparent = storage.create_task(title="Grandparent")
        parent = storage.create_task(title="Parent", parent_id=grandparent.id)
        child = storage.create_task(title="Child", parent_id=parent.id)
        
        result = get_task_tree(storage, grandparent.id)
        
        assert len(result["tree"]["children"]) == 1
        parent_node = result["tree"]["children"][0]
        assert len(parent_node["children"]) == 1
        assert parent_node["children"][0]["task"]["id"] == child.id
    
    def test_tree_nonexistent_task(self, storage):
        """Test tree with nonexistent task."""
        result = get_task_tree(storage, "nonexistent")
        
        assert "error" in result


class TestUpdateParentStatus:
    """Test parent status rollup."""
    
    def test_parent_done_when_all_children_done(self, storage):
        """Test parent marked done when all children done."""
        parent = storage.create_task(title="Parent")
        child1 = storage.create_task(title="Child 1", parent_id=parent.id)
        child2 = storage.create_task(title="Child 2", parent_id=parent.id)
        
        storage.update_task(child1.id, status="done")
        update_parent_status(storage, child1.id)
        
        # Parent should still be open (one child not done)
        parent_updated = storage.get_task(parent.id)
        assert parent_updated.status == "open"
        
        # Complete second child
        storage.update_task(child2.id, status="done")
        update_parent_status(storage, child2.id)
        
        # Now parent should be done
        parent_updated = storage.get_task(parent.id)
        assert parent_updated.status == "done"
    
    def test_parent_in_progress_when_child_in_progress(self, storage):
        """Test parent marked in_progress when child is in_progress."""
        parent = storage.create_task(title="Parent")
        child = storage.create_task(title="Child", parent_id=parent.id)
        
        storage.update_task(child.id, status="in_progress")
        update_parent_status(storage, child.id)
        
        parent_updated = storage.get_task(parent.id)
        assert parent_updated.status == "in_progress"
    
    def test_cancelled_children_count_as_done(self, storage):
        """Test cancelled children count as done for rollup."""
        parent = storage.create_task(title="Parent")
        child1 = storage.create_task(title="Child 1", parent_id=parent.id)
        child2 = storage.create_task(title="Child 2", parent_id=parent.id)
        
        storage.update_task(child1.id, status="done")
        storage.update_task(child2.id, status="cancelled")
        update_parent_status(storage, child2.id)
        
        parent_updated = storage.get_task(parent.id)
        assert parent_updated.status == "done"
    
    def test_no_parent_no_error(self, storage):
        """Test no error when task has no parent."""
        task = storage.create_task(title="No parent")
        
        # Should not raise
        update_parent_status(storage, task.id)
    
    def test_recursive_rollup(self, storage):
        """Test status rolls up recursively."""
        grandparent = storage.create_task(title="Grandparent")
        parent = storage.create_task(title="Parent", parent_id=grandparent.id)
        child = storage.create_task(title="Child", parent_id=parent.id)
        
        storage.update_task(child.id, status="done")
        update_parent_status(storage, child.id)
        
        parent_updated = storage.get_task(parent.id)
        grandparent_updated = storage.get_task(grandparent.id)
        
        assert parent_updated.status == "done"
        assert grandparent_updated.status == "done"


class TestGetSubtaskProgress:
    """Test subtask progress calculation."""
    
    def test_progress_no_children(self, storage):
        """Test progress with no children."""
        task = storage.create_task(title="No children")
        
        result = get_subtask_progress(storage, task.id)
        
        assert result["total"] == 0
        assert result["progress_percent"] == 0
    
    def test_progress_all_open(self, storage):
        """Test progress with all open tasks."""
        parent = storage.create_task(title="Parent")
        storage.create_task(title="Child 1", parent_id=parent.id)
        storage.create_task(title="Child 2", parent_id=parent.id)
        
        result = get_subtask_progress(storage, parent.id)
        
        assert result["total"] == 2
        assert result["open"] == 2
        assert result["done"] == 0
        assert result["progress_percent"] == 0
    
    def test_progress_partial(self, storage):
        """Test progress with partial completion."""
        parent = storage.create_task(title="Parent")
        child1 = storage.create_task(title="Child 1", parent_id=parent.id)
        storage.create_task(title="Child 2", parent_id=parent.id)
        
        storage.update_task(child1.id, status="done")
        
        result = get_subtask_progress(storage, parent.id)
        
        assert result["total"] == 2
        assert result["done"] == 1
        assert result["open"] == 1
        assert result["progress_percent"] == 50.0
    
    def test_progress_with_story_points(self, storage):
        """Test progress tracks story points."""
        parent = storage.create_task(title="Parent")
        child1 = storage.create_task(title="Child 1", parent_id=parent.id, story_points=3)
        child2 = storage.create_task(title="Child 2", parent_id=parent.id, story_points=5)
        
        storage.update_task(child1.id, status="done")
        
        result = get_subtask_progress(storage, parent.id)
        
        assert result["total_points"] == 8
        assert result["completed_points"] == 3
    
    def test_progress_excludes_cancelled_from_percent(self, storage):
        """Test cancelled tasks excluded from percentage calculation."""
        parent = storage.create_task(title="Parent")
        child1 = storage.create_task(title="Child 1", parent_id=parent.id)
        child2 = storage.create_task(title="Child 2", parent_id=parent.id)
        child3 = storage.create_task(title="Child 3", parent_id=parent.id)
        
        storage.update_task(child1.id, status="done")
        storage.update_task(child2.id, status="cancelled")
        
        result = get_subtask_progress(storage, parent.id)
        
        # 1 done out of 2 countable (3 total - 1 cancelled)
        assert result["total"] == 3
        assert result["cancelled"] == 1
        assert result["progress_percent"] == 50.0
    
    def test_progress_nonexistent_task(self, storage):
        """Test progress for nonexistent task."""
        result = get_subtask_progress(storage, "nonexistent")
        
        assert "error" in result


class TestSuggestDecomposition:
    """Test decomposition suggestions."""
    
    def test_suggest_for_large_task(self):
        """Test suggestions for large task."""
        task = Task(
            id="ch-large",
            title="Implement authentication",
            story_points=13,
        )
        
        suggestions = suggest_decomposition(task)
        
        assert len(suggestions) > 0
        assert any("Design" in s for s in suggestions)
    
    def test_suggest_for_epic(self):
        """Test suggestions for epic type."""
        task = Task(
            id="ch-epic",
            title="Add user dashboard",
            task_type="epic",
        )
        
        suggestions = suggest_decomposition(task)
        
        assert len(suggestions) > 0
    
    def test_suggest_for_api_task(self):
        """Test suggestions for API task."""
        task = Task(
            id="ch-api",
            title="Create REST API endpoint",
        )
        
        suggestions = suggest_decomposition(task)
        
        assert len(suggestions) > 0
        assert any("API" in s or "endpoint" in s for s in suggestions)
    
    def test_suggest_for_ui_task(self):
        """Test suggestions for UI task."""
        task = Task(
            id="ch-ui",
            title="Build login UI component",
        )
        
        suggestions = suggest_decomposition(task)
        
        assert len(suggestions) > 0
        assert any("component" in s.lower() for s in suggestions)
    
    def test_suggest_for_bug(self):
        """Test suggestions for bug type."""
        task = Task(
            id="ch-bug",
            title="Fix login error",
            task_type="bug",
        )
        
        suggestions = suggest_decomposition(task)
        
        assert len(suggestions) > 0
        assert any("fix" in s.lower() or "reproduce" in s.lower() for s in suggestions)
    
    def test_suggest_for_small_task(self):
        """Test no suggestions for small task."""
        task = Task(
            id="ch-small",
            title="Update README",
            story_points=1,
        )
        
        suggestions = suggest_decomposition(task)
        
        # Small tasks may have no suggestions
        assert isinstance(suggestions, list)
