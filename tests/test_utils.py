"""Tests for utils module."""

import json
import tempfile
from pathlib import Path

import pytest

from chisel.utils import (
    find_chisel_root,
    format_json_output,
    format_priority,
    format_status,
    generate_task_id,
    parse_labels,
    truncate_string,
)


class TestGenerateTaskId:
    """Test task ID generation."""
    
    def test_default_prefix(self):
        """Test ID generation with default prefix."""
        task_id = generate_task_id()
        
        assert task_id.startswith("ch-")
        assert len(task_id) == 9  # "ch-" + 6 chars
    
    def test_custom_prefix(self):
        """Test ID generation with custom prefix."""
        task_id = generate_task_id(prefix="task")
        
        assert task_id.startswith("task-")
        assert len(task_id) == 11  # "task-" + 6 chars
    
    def test_unique_ids(self):
        """Test that generated IDs are unique."""
        ids = set()
        for _ in range(100):
            task_id = generate_task_id()
            ids.add(task_id)
        
        # All 100 IDs should be unique
        assert len(ids) == 100
    
    def test_id_format(self):
        """Test that ID follows expected format."""
        task_id = generate_task_id()
        
        # Should be prefix-hexchars
        parts = task_id.split("-")
        assert len(parts) == 2
        assert parts[0] == "ch"
        # Hex chars only
        assert all(c in "0123456789abcdef" for c in parts[1])


class TestFindChiselRoot:
    """Test project root discovery."""
    
    def test_finds_root_in_current_dir(self):
        """Test finding root when in project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            chisel_dir = project_path / ".chisel"
            chisel_dir.mkdir()
            (chisel_dir / "chisel.db").touch()
            
            root = find_chisel_root(project_path)
            
            assert root == project_path
    
    def test_finds_root_in_parent(self):
        """Test finding root when in subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            chisel_dir = project_path / ".chisel"
            chisel_dir.mkdir()
            (chisel_dir / "chisel.db").touch()
            
            # Create nested directory
            nested = project_path / "src" / "deep" / "nested"
            nested.mkdir(parents=True)
            
            root = find_chisel_root(nested)
            
            assert root == project_path
    
    def test_returns_none_when_not_found(self):
        """Test returns None when no project found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = find_chisel_root(Path(tmpdir))
            
            assert root is None
    
    def test_returns_none_without_db(self):
        """Test returns None when .chisel exists but no db."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            chisel_dir = project_path / ".chisel"
            chisel_dir.mkdir()
            # No chisel.db file
            
            root = find_chisel_root(project_path)
            
            assert root is None


class TestFormatJsonOutput:
    """Test JSON formatting."""
    
    def test_pretty_format(self):
        """Test pretty JSON output."""
        data = {"key": "value", "number": 42}
        
        output = format_json_output(data, pretty=True)
        
        assert "  " in output  # Has indentation
        assert json.loads(output) == data
    
    def test_compact_format(self):
        """Test compact JSON output."""
        data = {"key": "value", "number": 42}
        
        output = format_json_output(data, pretty=False)
        
        assert "  " not in output  # No indentation
        assert json.loads(output) == data
    
    def test_handles_datetime(self):
        """Test handling datetime objects."""
        from datetime import datetime
        
        data = {"time": datetime(2024, 1, 15, 10, 30)}
        
        output = format_json_output(data)
        
        # Should not raise, datetime converted to string
        parsed = json.loads(output)
        assert "2024" in parsed["time"]
    
    def test_handles_nested_structures(self):
        """Test handling nested data structures."""
        data = {
            "tasks": [
                {"id": "ch-1", "title": "Task 1"},
                {"id": "ch-2", "title": "Task 2"},
            ],
            "meta": {"count": 2},
        }
        
        output = format_json_output(data)
        
        parsed = json.loads(output)
        assert len(parsed["tasks"]) == 2


class TestParseLabels:
    """Test label parsing."""
    
    def test_parse_single_label(self):
        """Test parsing single label."""
        labels = parse_labels("bug")
        
        assert labels == ["bug"]
    
    def test_parse_multiple_labels(self):
        """Test parsing multiple labels."""
        labels = parse_labels("bug,urgent,backend")
        
        assert labels == ["bug", "urgent", "backend"]
    
    def test_parse_with_spaces(self):
        """Test parsing labels with spaces."""
        labels = parse_labels("bug, urgent, backend")
        
        assert labels == ["bug", "urgent", "backend"]
    
    def test_parse_empty_string(self):
        """Test parsing empty string."""
        labels = parse_labels("")
        
        assert labels == []
    
    def test_parse_none(self):
        """Test parsing None."""
        labels = parse_labels(None)
        
        assert labels == []
    
    def test_parse_filters_empty_labels(self):
        """Test that empty labels are filtered."""
        labels = parse_labels("bug,,urgent")
        
        assert labels == ["bug", "urgent"]
    
    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string."""
        labels = parse_labels("   ")
        
        assert labels == []


class TestFormatPriority:
    """Test priority formatting."""
    
    def test_format_critical(self):
        """Test formatting critical priority."""
        assert format_priority(0) == "P0 (critical)"
    
    def test_format_high(self):
        """Test formatting high priority."""
        assert format_priority(1) == "P1 (high)"
    
    def test_format_medium(self):
        """Test formatting medium priority."""
        assert format_priority(2) == "P2 (medium)"
    
    def test_format_low(self):
        """Test formatting low priority."""
        assert format_priority(3) == "P3 (low)"
    
    def test_format_backlog(self):
        """Test formatting backlog priority."""
        assert format_priority(4) == "P4 (backlog)"
    
    def test_format_unknown(self):
        """Test formatting unknown priority."""
        assert format_priority(99) == "P99"


class TestFormatStatus:
    """Test status formatting."""
    
    def test_format_open(self):
        """Test formatting open status."""
        assert format_status("open") == "[ ]"
    
    def test_format_in_progress(self):
        """Test formatting in_progress status."""
        assert format_status("in_progress") == "[>]"
    
    def test_format_blocked(self):
        """Test formatting blocked status."""
        assert format_status("blocked") == "[!]"
    
    def test_format_review(self):
        """Test formatting review status."""
        assert format_status("review") == "[?]"
    
    def test_format_done(self):
        """Test formatting done status."""
        assert format_status("done") == "[x]"
    
    def test_format_cancelled(self):
        """Test formatting cancelled status."""
        assert format_status("cancelled") == "[-]"
    
    def test_format_custom(self):
        """Test formatting custom status."""
        assert format_status("custom") == "[custom]"


class TestTruncateString:
    """Test string truncation."""
    
    def test_short_string_unchanged(self):
        """Test short string is not truncated."""
        s = "Short string"
        
        assert truncate_string(s, 50) == s
    
    def test_exact_length_unchanged(self):
        """Test string at exact length is not truncated."""
        s = "x" * 50
        
        assert truncate_string(s, 50) == s
    
    def test_long_string_truncated(self):
        """Test long string is truncated."""
        s = "x" * 100
        
        result = truncate_string(s, 50)
        
        assert len(result) == 50
        assert result.endswith("...")
    
    def test_truncated_with_ellipsis(self):
        """Test truncated string ends with ellipsis."""
        s = "This is a very long string that needs truncation"
        
        result = truncate_string(s, 20)
        
        assert len(result) == 20
        assert result == "This is a very lo..."
    
    def test_custom_max_length(self):
        """Test custom max length."""
        s = "Hello world"
        
        result = truncate_string(s, 8)
        
        assert len(result) == 8
        assert result == "Hello..."
    
    def test_default_max_length(self):
        """Test default max length of 50."""
        s = "x" * 100
        
        result = truncate_string(s)
        
        assert len(result) == 50
