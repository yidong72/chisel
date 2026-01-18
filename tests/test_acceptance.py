"""Acceptance tests demonstrating complete use cases.

These tests simulate realistic workflows that a developer or AI agent
would follow when using Chisel for task management.
"""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from chisel.cli import main
from chisel.storage import init_project


class TestFeatureDevelopmentWorkflow:
    """
    Acceptance test: Complete feature development workflow.
    
    Scenario: A developer needs to implement a user authentication feature.
    
    This test demonstrates:
    1. Initializing a project
    2. Creating an epic for the feature
    3. Breaking it down into subtasks
    4. Adding dependencies between tasks
    5. Working through tasks in order
    6. Using quality hooks for validation
    7. Completing all tasks and the epic
    """
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()
    
    @pytest.fixture
    def project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def run_cmd(self, runner, project_dir, *args):
        """Helper to run CLI command with JSON output."""
        result = runner.invoke(
            main, 
            ["--project", str(project_dir)] + list(args) + ["--json"]
        )
        if result.output.strip():
            return json.loads(result.output), result.exit_code
        return {}, result.exit_code
    
    def test_complete_feature_development_workflow(self, runner, project_dir):
        """
        Complete acceptance test for feature development workflow.
        
        This simulates a developer implementing a "User Authentication" feature:
        
        1. Initialize project
        2. Create epic: "User Authentication"
        3. Decompose into subtasks:
           - Design auth flow
           - Implement OAuth providers
           - Create login UI
           - Add session management
           - Write tests
        4. Set up dependencies (tests depend on implementation)
        5. Add quality hook (run tests before closing)
        6. Work through tasks in priority order
        7. Complete the epic
        """
        
        # =====================================================================
        # Step 1: Initialize the project
        # =====================================================================
        result = runner.invoke(main, ["--project", str(project_dir), "init", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "project_root" in data
        print(f"\n✓ Project initialized at {data['project_root']}")
        
        # =====================================================================
        # Step 2: Create the epic
        # =====================================================================
        data, code = self.run_cmd(
            runner, project_dir,
            "create", "User Authentication",
            "-t", "epic",
            "-p", "1",
            "-d", "Implement complete user authentication with OAuth support"
        )
        assert code == 0
        epic_id = data["task"]["id"]
        assert data["task"]["task_type"] == "epic"
        assert data["task"]["priority"] == 1
        print(f"✓ Created epic: {epic_id} - User Authentication")
        
        # =====================================================================
        # Step 3: Decompose epic into subtasks
        # =====================================================================
        data, code = self.run_cmd(
            runner, project_dir,
            "decompose", epic_id,
            "Design authentication flow",
            "Implement OAuth providers",
            "Create login UI components",
            "Add session management",
            "Write integration tests",
            "--points", "2,5,5,3,3"
        )
        assert code == 0
        assert len(data["subtasks"]) == 5
        subtasks = {s["title"]: s["id"] for s in data["subtasks"]}
        print(f"✓ Decomposed into {len(subtasks)} subtasks")
        
        # Verify story points
        assert data["subtasks"][0]["story_points"] == 2  # Design
        assert data["subtasks"][1]["story_points"] == 5  # OAuth
        assert data["subtasks"][4]["story_points"] == 3  # Tests
        
        # =====================================================================
        # Step 4: Add dependencies
        # Tests depend on implementation being done first
        # =====================================================================
        test_task_id = subtasks["Write integration tests"]
        oauth_task_id = subtasks["Implement OAuth providers"]
        ui_task_id = subtasks["Create login UI components"]
        session_task_id = subtasks["Add session management"]
        design_task_id = subtasks["Design authentication flow"]
        
        # Tests blocked by implementation tasks
        self.run_cmd(runner, project_dir, "dep", "add", test_task_id, "--blocked-by", oauth_task_id)
        self.run_cmd(runner, project_dir, "dep", "add", test_task_id, "--blocked-by", ui_task_id)
        self.run_cmd(runner, project_dir, "dep", "add", test_task_id, "--blocked-by", session_task_id)
        
        # Implementation blocked by design
        self.run_cmd(runner, project_dir, "dep", "add", oauth_task_id, "--blocked-by", design_task_id)
        self.run_cmd(runner, project_dir, "dep", "add", ui_task_id, "--blocked-by", design_task_id)
        self.run_cmd(runner, project_dir, "dep", "add", session_task_id, "--blocked-by", design_task_id)
        
        print("✓ Added dependencies: Design → Implementation → Tests")
        
        # =====================================================================
        # Step 5: Add quality hook
        # =====================================================================
        data, code = self.run_cmd(
            runner, project_dir,
            "hook", "set", "pre-close", "echo 'Running validation...'"
        )
        assert code == 0
        print("✓ Added pre-close quality hook")
        
        # =====================================================================
        # Step 6: Check what's ready to work on
        # =====================================================================
        data, code = self.run_cmd(runner, project_dir, "ready")
        assert code == 0
        ready_ids = [t["id"] for t in data["tasks"]]
        
        # Only design should be ready (others are blocked)
        assert design_task_id in ready_ids
        assert oauth_task_id not in ready_ids
        assert test_task_id not in ready_ids
        print(f"✓ Verified only design task is ready (others blocked)")
        
        # =====================================================================
        # Step 7: Work through tasks in order
        # =====================================================================
        
        # --- Complete Design ---
        data, code = self.run_cmd(
            runner, project_dir,
            "update", design_task_id, "--status", "in_progress"
        )
        assert code == 0
        assert data["task"]["status"] == "in_progress"
        
        data, code = self.run_cmd(
            runner, project_dir,
            "close", design_task_id, "--reason", "Auth flow designed and documented"
        )
        assert code == 0
        assert data["task"]["status"] == "done"
        print(f"✓ Completed: Design authentication flow")
        
        # Now implementation tasks should be ready
        data, code = self.run_cmd(runner, project_dir, "ready")
        ready_ids = [t["id"] for t in data["tasks"]]
        assert oauth_task_id in ready_ids
        assert ui_task_id in ready_ids
        assert session_task_id in ready_ids
        assert test_task_id not in ready_ids  # Still blocked
        print("✓ Implementation tasks now ready")
        
        # --- Complete OAuth Implementation ---
        self.run_cmd(runner, project_dir, "update", oauth_task_id, "--status", "in_progress")
        data, code = self.run_cmd(
            runner, project_dir,
            "close", oauth_task_id, "--reason", "Google and GitHub OAuth implemented"
        )
        assert code == 0
        print(f"✓ Completed: Implement OAuth providers")
        
        # --- Complete UI ---
        self.run_cmd(runner, project_dir, "update", ui_task_id, "--status", "in_progress")
        data, code = self.run_cmd(
            runner, project_dir,
            "close", ui_task_id, "--reason", "Login/signup components created"
        )
        assert code == 0
        print(f"✓ Completed: Create login UI components")
        
        # --- Complete Session Management ---
        self.run_cmd(runner, project_dir, "update", session_task_id, "--status", "in_progress")
        data, code = self.run_cmd(
            runner, project_dir,
            "close", session_task_id, "--reason", "JWT session management implemented"
        )
        assert code == 0
        print(f"✓ Completed: Add session management")
        
        # Now tests should be ready
        data, code = self.run_cmd(runner, project_dir, "ready")
        ready_ids = [t["id"] for t in data["tasks"]]
        assert test_task_id in ready_ids
        print("✓ Test task now ready (all blockers done)")
        
        # --- Complete Tests ---
        self.run_cmd(runner, project_dir, "update", test_task_id, "--status", "in_progress")
        data, code = self.run_cmd(
            runner, project_dir,
            "close", test_task_id, "--reason", "All integration tests passing"
        )
        assert code == 0
        print(f"✓ Completed: Write integration tests")
        
        # =====================================================================
        # Step 8: Verify epic is automatically completed
        # =====================================================================
        data, code = self.run_cmd(runner, project_dir, "show", epic_id)
        assert code == 0
        assert data["task"]["status"] == "done"
        print(f"✓ Epic automatically marked as done (all subtasks complete)")
        
        # =====================================================================
        # Step 9: View final tree
        # =====================================================================
        data, code = self.run_cmd(runner, project_dir, "tree", epic_id)
        assert code == 0
        assert data["tree"]["task"]["status"] == "done"
        assert len(data["tree"]["children"]) == 5
        assert all(child["task"]["status"] == "done" for child in data["tree"]["children"])
        print("✓ All tasks in tree are done")
        
        # =====================================================================
        # Step 10: Verify no tasks remain
        # =====================================================================
        data, code = self.run_cmd(runner, project_dir, "ready")
        assert code == 0
        assert len(data["tasks"]) == 0
        print("✓ No tasks remaining in ready queue")
        
        data, code = self.run_cmd(runner, project_dir, "list", "--status", "open")
        assert code == 0
        assert len(data["tasks"]) == 0
        print("✓ No open tasks remaining")
        
        print("\n" + "=" * 60)
        print("ACCEPTANCE TEST PASSED: Feature Development Workflow Complete")
        print("=" * 60)


class TestBugTriageWorkflow:
    """
    Acceptance test: Bug triage and fix workflow.
    
    Scenario: A bug is reported, triaged, fixed, and verified.
    """
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    @pytest.fixture  
    def project_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            init_project(project_path)
            yield project_path
    
    def run_cmd(self, runner, project_dir, *args):
        result = runner.invoke(
            main,
            ["--project", str(project_dir)] + list(args) + ["--json"]
        )
        if result.output.strip():
            return json.loads(result.output), result.exit_code
        return {}, result.exit_code
    
    def test_bug_triage_and_fix_workflow(self, runner, project_dir):
        """
        Test bug triage workflow:
        
        1. Create high-priority bug
        2. Add details and acceptance criteria
        3. Find it in ready queue
        4. Work on the fix
        5. Validate and close
        """
        
        # Create bug report
        data, code = self.run_cmd(
            runner, project_dir,
            "create", "Login fails with special characters in password",
            "-t", "bug",
            "-p", "0",  # Critical
            "-d", "Users cannot log in if password contains < or > characters",
            "--labels", "auth,security,critical"
        )
        assert code == 0
        bug_id = data["task"]["id"]
        assert data["task"]["task_type"] == "bug"
        assert data["task"]["priority"] == 0
        print(f"\n✓ Created critical bug: {bug_id}")
        
        # Bug should be at top of ready queue (priority 0)
        data, code = self.run_cmd(runner, project_dir, "ready", "--limit", "1")
        assert code == 0
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == bug_id
        print("✓ Bug is highest priority in ready queue")
        
        # Start working on fix
        data, code = self.run_cmd(
            runner, project_dir,
            "update", bug_id, "--status", "in_progress"
        )
        assert code == 0
        print("✓ Started working on bug fix")
        
        # Complete the fix
        data, code = self.run_cmd(
            runner, project_dir,
            "close", bug_id,
            "--reason", "Fixed input sanitization, added regression test for special chars"
        )
        assert code == 0
        assert data["task"]["status"] == "done"
        print("✓ Bug fixed and closed")
        
        # Verify it's no longer in ready queue
        data, code = self.run_cmd(runner, project_dir, "ready")
        assert code == 0
        assert not any(t["id"] == bug_id for t in data["tasks"])
        print("✓ Bug no longer in ready queue")
        
        print("\n" + "=" * 60)
        print("ACCEPTANCE TEST PASSED: Bug Triage Workflow Complete")
        print("=" * 60)
