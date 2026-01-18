"""Utility functions for Chisel task manager."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


def generate_task_id(prefix: str = "ch") -> str:
    """Generate a unique task ID.
    
    Args:
        prefix: Prefix for the task ID (default: "ch")
    
    Returns:
        A unique task ID like "ch-abc123"
    """
    # Use timestamp + random bytes for uniqueness
    timestamp = str(time.time_ns())
    hash_input = timestamp.encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()[:6]
    return f"{prefix}-{hash_digest}"


def find_chisel_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Walk up directory tree to find nearest .chisel/ directory.
    
    Args:
        start_path: Starting directory (defaults to current working directory)
    
    Returns:
        Path to the project root (parent of .chisel/) or None if not found
    """
    current = start_path or Path.cwd()
    current = current.resolve()
    
    while current != current.parent:
        chisel_dir = current / ".chisel"
        if chisel_dir.is_dir() and (chisel_dir / "chisel.db").exists():
            return current
        current = current.parent
    
    # Check root as well
    chisel_dir = current / ".chisel"
    if chisel_dir.is_dir() and (chisel_dir / "chisel.db").exists():
        return current
    
    return None


def format_json_output(data: Any, pretty: bool = True) -> str:
    """Format data as JSON string.
    
    Args:
        data: Data to serialize
        pretty: Whether to use indentation (default: True)
    
    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)


def parse_labels(labels_str: Optional[str]) -> list[str]:
    """Parse a comma-separated label string into a list.
    
    Args:
        labels_str: Comma-separated labels (e.g., "bug,urgent,frontend")
    
    Returns:
        List of labels
    """
    if not labels_str:
        return []
    return [label.strip() for label in labels_str.split(",") if label.strip()]


def format_priority(priority: int) -> str:
    """Format priority number as human-readable string.
    
    Args:
        priority: Priority level (0-4)
    
    Returns:
        Human-readable priority string
    """
    priority_names = {
        0: "P0 (critical)",
        1: "P1 (high)",
        2: "P2 (medium)",
        3: "P3 (low)",
        4: "P4 (backlog)",
    }
    return priority_names.get(priority, f"P{priority}")


def format_status(status: str) -> str:
    """Format status with color hints for CLI display.
    
    Args:
        status: Task status
    
    Returns:
        Formatted status string
    """
    status_icons = {
        "open": "[ ]",
        "in_progress": "[>]",
        "blocked": "[!]",
        "review": "[?]",
        "done": "[x]",
        "cancelled": "[-]",
    }
    return status_icons.get(status, f"[{status}]")


def truncate_string(s: str, max_length: int = 50) -> str:
    """Truncate a string with ellipsis if too long.
    
    Args:
        s: String to truncate
        max_length: Maximum length
    
    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."
