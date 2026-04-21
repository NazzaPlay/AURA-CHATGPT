#!/usr/bin/env python
"""
Validation script for Operational Supervisor V0.3
This script validates synchronization between queue, registry, and log
"""

import json
import os
from datetime import datetime

def validate_registry_queue_sync():
    """Validate that registry and queue have synchronized tasks"""
    print("Validating registry and queue synchronization...")
    
    # Load registry tasks
    with open('ops/assistant_ops_registry.json', 'r') as f:
        registry_data = json.load(f)
    
    registry_tasks = {task['task_id']: task for task in registry_data['tasks']}
    registry_task_ids = set(registry_tasks.keys())
    
    # Read queue file and extract task info
    with open('ops/task_queue.md', 'r') as f:
        queue_content = f.read()
    
    queue_task_ids = set()
    queue_priorities = {}
    queue_statuses = {}
    
    lines = queue_content.split('\n')
    current_task_id = None
    
    for line in lines:
        if line.strip().startswith("#### Task ID:"):
            current_task_id = line.split(":", 1)[1].strip()
            queue_task_ids.add(current_task_id)
        elif line.strip().startswith("- Priority:") and current_task_id:
            priority = int(line.split(":")[1].strip())
            queue_priorities[current_task_id] = priority
        elif line.strip().startswith("- Status:") and current_task_id:
            status = line.split(":")[1].strip()
            queue_statuses[current_task_id] = status
    
    # Compare sets
    print(f"Registry has {len(registry_task_ids)} tasks: {registry_task_ids}")
    print(f"Queue has {len(queue_task_ids)} tasks: {queue_task_ids}")
    
    if registry_task_ids == queue_task_ids:
        print("✓ Registry and queue task IDs match")
    else:
        print(f"✗ Registry and queue task IDs mismatch: registry={registry_task_ids}, queue={queue_task_ids}")
        return False
    
    # Check priorities match
    for task_id in registry_task_ids:
        reg_priority = registry_tasks[task_id]['priority']
        if task_id in queue_priorities:
            queue_priority = queue_priorities[task_id]
            if reg_priority == queue_priority:
                print(f"✓ Priority match for {task_id}: {reg_priority}")
            else:
                print(f"✗ Priority mismatch for {task_id}: registry={reg_priority}, queue={queue_priority}")
                return False
        else:
            print(f"✗ Task {task_id} not found in queue")
            return False
    
    # Check statuses match
    for task_id in registry_task_ids:
        reg_status = registry_tasks[task_id]['status']
        if task_id in queue_statuses:
            queue_status = queue_statuses[task_id]
            if reg_status == queue_status:
                print(f"✓ Status match for {task_id}: {reg_status}")
            else:
                print(f"✗ Status mismatch for {task_id}: registry={reg_status}, queue={queue_status}")
                return False
        else:
            print(f"✗ Task {task_id} not found in queue statuses")
            return False
    
    return True

def validate_registry_log_sync():
    """Validate that registry and log have synchronized tasks"""
    print("\nValidating registry and log synchronization...")
    
    # Load registry tasks
    with open('ops/assistant_ops_registry.json', 'r') as f:
        registry_data = json.load(f)
    
    registry_task_ids = {task['task_id'] for task in registry_data['tasks']}
    
    # Read log file and extract task IDs
    with open('ops/execution_log.md', 'r') as f:
        log_content = f.read()
    
    log_task_ids = set()
    for line in log_content.split('\n'):
        if line.strip().startswith("- Task ID:"):
            task_id = line.split(":", 1)[1].strip()
            log_task_ids.add(task_id)
    
    print(f"Registry has {len(registry_task_ids)} tasks: {registry_task_ids}")
    print(f"Log has {len(log_task_ids)} tasks: {log_task_ids}")
    
    if log_task_ids.issubset(registry_task_ids):
        print("✓ All log entries correspond to registry tasks")
        return True
    else:
        missing_from_registry = log_task_ids - registry_task_ids
        print(f"✗ Log entries reference non-existent registry tasks: {missing_from_registry}")
        return False

def validate_helper_functions():
    """Validate that helper functions work as expected"""
    print("\nValidating helper functions...")
    
    try:
        from backend.app.routing_neuron.admin.initializer import (
            initialize_operational_supervisor,
            sync_registries,
            update_execution_log,
            validate_task_exists,
            get_task_by_id,
            update_task_status
        )
        
        print("✓ All helper functions imported successfully")
        
        # Test that functions exist and are callable
        assert callable(initialize_operational_supervisor)
        assert callable(sync_registries)
        assert callable(update_execution_log)
        assert callable(validate_task_exists)
        assert callable(get_task_by_id)
        assert callable(update_task_status)
        
        print("✓ All helper functions are callable")
        
        # Test basic functionality
        exists = validate_task_exists("task_001")
        if exists:
            print("✓ validate_task_exists works correctly")
        else:
            print("✗ validate_task_exists failed")
            return False
            
        task = get_task_by_id("task_001")
        if task and task['task_id'] == "task_001":
            print("✓ get_task_by_id works correctly")
        else:
            print("✗ get_task_by_id failed")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Helper function validation failed: {e}")
        return False

def main():
    print("=== Operational Supervisor V0.3 Validation ===\n")
    
    results = []
    
    # Validate registry and queue sync
    results.append(validate_registry_queue_sync())
    
    # Validate registry and log sync
    results.append(validate_registry_log_sync())
    
    # Validate helper functions
    results.append(validate_helper_functions())
    
    print(f"\n=== Results ===")
    print(f"Registry-Queue Sync: {'PASS' if results[0] else 'FAIL'}")
    print(f"Registry-Log Sync: {'PASS' if results[1] else 'FAIL'}")
    print(f"Helper Functions: {'PASS' if results[2] else 'FAIL'}")
    
    overall_result = all(results)
    print(f"Overall: {'PASS' if overall_result else 'FAIL'}")
    
    if overall_result:
        print("\n✓ All validations passed! Operational Supervisor V0.3 is ready.")
    else:
        print("\n✗ Some validations failed. Please review the issues above.")
    
    return overall_result

if __name__ == "__main__":
    main()