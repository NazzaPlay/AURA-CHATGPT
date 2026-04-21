"""
Unit tests for the Operational Supervisor V0.3
Tests synchronization between queue, registry, and log
"""

import unittest
import json
import os
from backend.app.routing_neuron.admin.initializer import (
    initialize_operational_supervisor,
    sync_registries,
    update_execution_log,
    validate_task_exists
)


class TestOperationalSupervisor(unittest.TestCase):
    """Test cases for Operational Supervisor V0.3 components"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_task_id = "task_001"
        self.test_registry_path = "ops/assistant_ops_registry.json"
        self.test_queue_path = "ops/task_queue.md"
        self.test_log_path = "ops/execution_log.md"

    def test_initialize_operational_supervisor(self):
        """Test that operational supervisor initializes without error."""
        try:
            initialize_operational_supervisor()
            self.assertTrue(True)  # If we reach here, no exception occurred
        except Exception as e:
            self.fail(f"initialize_operational_supervisor raised {type(e).__name__}: {e}")

    def test_sync_registries_success(self):
        """Test that registry synchronization works."""
        result = sync_registries()
        self.assertTrue(result)

    def test_validate_task_exists_positive(self):
        """Test that validate_task_exists correctly identifies existing tasks."""
        result = validate_task_exists(self.test_task_id)
        self.assertTrue(result, f"Task {self.test_task_id} should exist in registry")

    def test_validate_task_exists_negative(self):
        """Test that validate_task_exists correctly identifies non-existing tasks."""
        result = validate_task_exists("nonexistent_task_999")
        self.assertFalse(result, "Non-existent task should not exist in registry")

    def test_update_execution_log(self):
        """Test that execution log can be updated."""
        log_entry = update_execution_log(
            task_id=self.test_task_id,
            status="completed",
            result="success",
            notes="Test execution completed successfully"
        )
        
        self.assertEqual(log_entry["task_id"], self.test_task_id)
        self.assertIsNotNone(log_entry["timestamp"])
        self.assertEqual(log_entry["status"], "completed")
        self.assertEqual(log_entry["result"], "success")

    def test_registry_queue_log_sync_ids(self):
        """Test that IDs in registry, queue, and log are consistent."""
        # Load registry tasks
        with open(self.test_registry_path, 'r') as f:
            registry_data = json.load(f)
        
        registry_task_ids = {task['task_id'] for task in registry_data['tasks']}
        
        # Read queue file and extract task IDs
        with open(self.test_queue_path, 'r') as f:
            queue_content = f.read()
        
        queue_task_ids = set()
        for line in queue_content.split('\n'):
            if line.strip().startswith("#### Task ID:"):
                task_id = line.split(":", 1)[1].strip()
                queue_task_ids.add(task_id)
        
        # Read log file and extract task IDs
        with open(self.test_log_path, 'r') as f:
            log_content = f.read()
        
        log_task_ids = set()
        for line in log_content.split('\n'):
            if line.strip().startswith("- Task ID:"):
                task_id = line.split(":", 1)[1].strip()
                log_task_ids.add(task_id)
        
        # Check that all sets of task IDs are equal
        self.assertEqual(registry_task_ids, queue_task_ids, 
                         "Registry and queue task IDs should match")
        self.assertEqual(queue_task_ids, log_task_ids, 
                         "Queue and log task IDs should match")
        
    def test_registry_queue_priority_sync(self):
        """Test that priorities in registry and queue are consistent."""
        # Load registry tasks
        with open(self.test_registry_path, 'r') as f:
            registry_data = json.load(f)
        
        registry_priorities = {}
        for task in registry_data['tasks']:
            registry_priorities[task['task_id']] = task['priority']
        
        # Read queue file and extract priorities
        with open(self.test_queue_path, 'r') as f:
            queue_content = f.read()
        
        queue_priorities = {}
        lines = queue_content.split('\n')
        current_task_id = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith("#### Task ID:"):
                current_task_id = line.split(":", 1)[1].strip()
            elif line.strip().startswith("- Priority:") and current_task_id:
                priority = int(line.split(":")[1].strip())
                queue_priorities[current_task_id] = priority
        
        # Check that priorities match
        for task_id, priority in registry_priorities.items():
            self.assertIn(task_id, queue_priorities, f"Task {task_id} should have a priority in queue")
            self.assertEqual(priority, queue_priorities[task_id], 
                           f"Priority mismatch for task {task_id}: registry={priority}, queue={queue_priorities[task_id]}")

    def test_registry_queue_status_sync(self):
        """Test that statuses in registry and queue are consistent."""
        # Load registry tasks
        with open(self.test_registry_path, 'r') as f:
            registry_data = json.load(f)
        
        registry_statuses = {}
        for task in registry_data['tasks']:
            registry_statuses[task['task_id']] = task['status']
        
        # Read queue file and extract statuses
        with open(self.test_queue_path, 'r') as f:
            queue_content = f.read()
        
        queue_statuses = {}
        lines = queue_content.split('\n')
        current_task_id = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith("#### Task ID:"):
                current_task_id = line.split(":", 1)[1].strip()
            elif line.strip().startswith("- Status:") and current_task_id:
                status = line.split(":")[1].strip()
                queue_statuses[current_task_id] = status
        
        # Check that statuses match
        for task_id, status in registry_statuses.items():
            self.assertIn(task_id, queue_statuses, f"Task {task_id} should have a status in queue")
            self.assertEqual(status, queue_statuses[task_id], 
                           f"Status mismatch for task {task_id}: registry={status}, queue={queue_statuses[task_id]}")


if __name__ == '__main__':
    # Run the tests
    unittest.main()