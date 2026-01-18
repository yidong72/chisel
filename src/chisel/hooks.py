"""Quality hooks for Chisel task manager."""

import subprocess
from typing import Optional

from chisel.storage import Storage
from chisel.utils import find_chisel_root


def run_hooks(
    storage: Storage,
    event: str,
    task_id: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> list[dict]:
    """Run all hooks for a given event.
    
    Args:
        storage: Storage instance
        event: Event name (pre-close, post-create, etc.)
        task_id: Task ID (passed as environment variable)
        working_dir: Working directory for commands (defaults to project root)
    
    Returns:
        List of hook results with success status and output
    """
    hooks = storage.get_hooks(event)
    
    if not hooks:
        return []
    
    # Determine working directory
    if working_dir is None:
        root = find_chisel_root()
        working_dir = str(root) if root else None
    
    results = []
    
    for hook in hooks:
        if not hook.enabled:
            continue
        
        result = run_hook(hook.command, task_id, working_dir)
        result["hook_id"] = hook.id
        result["event"] = hook.event
        results.append(result)
    
    return results


def run_hook(
    command: str,
    task_id: Optional[str] = None,
    working_dir: Optional[str] = None,
    timeout: int = 300,
) -> dict:
    """Run a single hook command.
    
    Args:
        command: Shell command to run
        task_id: Task ID (passed as environment variable)
        working_dir: Working directory for the command
        timeout: Command timeout in seconds
    
    Returns:
        Dictionary with success status, output, and return code
    """
    import os
    
    # Set up environment
    env = os.environ.copy()
    if task_id:
        env["CHISEL_TASK_ID"] = task_id
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            env=env,
            timeout=timeout,
        )
        
        return {
            "command": command,
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
        }
    
    except Exception as e:
        return {
            "command": command,
            "success": False,
            "return_code": -1,
            "stdout": "",
            "stderr": str(e),
        }


def validate_task(storage: Storage, task_id: str) -> dict:
    """Run all validation hooks for a task.
    
    Args:
        storage: Storage instance
        task_id: Task ID to validate
    
    Returns:
        Dictionary with validation results
    """
    task = storage.get_task(task_id)
    
    if task is None:
        return {
            "valid": False,
            "error": f"Task {task_id} not found",
            "results": [],
        }
    
    # Run pre-close hooks as validation
    results = run_hooks(storage, "pre-close", task_id)
    
    all_passed = all(r["success"] for r in results)
    
    # Calculate quality score based on hook results
    if results:
        passed_count = sum(1 for r in results if r["success"])
        quality_score = passed_count / len(results)
        
        # Update task with quality score
        storage.update_task(task_id, quality_score=quality_score)
    else:
        quality_score = None
    
    return {
        "valid": all_passed,
        "quality_score": quality_score,
        "results": results,
    }


# Common hook templates
HOOK_TEMPLATES = {
    "pytest": "pytest tests/ -q",
    "pytest-cov": "pytest tests/ --cov --cov-fail-under=80",
    "ruff": "ruff check .",
    "ruff-fix": "ruff check --fix .",
    "mypy": "mypy src/",
    "black": "black --check .",
    "isort": "isort --check-only .",
    "eslint": "eslint .",
    "prettier": "prettier --check .",
    "cargo-test": "cargo test",
    "cargo-clippy": "cargo clippy -- -D warnings",
    "go-test": "go test ./...",
    "go-vet": "go vet ./...",
}


def get_hook_template(name: str) -> Optional[str]:
    """Get a hook command template by name.
    
    Args:
        name: Template name
    
    Returns:
        Hook command or None if not found
    """
    return HOOK_TEMPLATES.get(name)


def list_hook_templates() -> dict[str, str]:
    """Get all available hook templates.
    
    Returns:
        Dictionary of template names to commands
    """
    return HOOK_TEMPLATES.copy()
