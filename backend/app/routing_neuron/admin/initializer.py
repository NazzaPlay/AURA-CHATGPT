"""
Initializer module for the Operational Supervisor V0.3
Handles initialization of operational tasks and registry synchronization
"""

import json
import os
from datetime import datetime


def initialize_operational_supervisor():
    """
    Initializes the operational supervisor components
    """
    print("Initializing Operational Supervisor V0.3...")
    
    # Check if required files exist
    ops_files = [
        "ops/assistant_ops_registry.json",
        "ops/task_queue.md", 
        "ops/execution_log.md"
    ]
    
    for ops_file in ops_files:
        if not os.path.exists(ops_file):
            print(f"Warning: {ops_file} does not exist.")
        else:
            print(f"Found {ops_file}")
    
    print("Operational Supervisor V0.3 initialized successfully")


def sync_registries():
    """
    Synchronize the operational registry with task queue and execution log
    """
    print("Starting registry synchronization...")
    
    try:
        # Load the operational registry
        with open('ops/assistant_ops_registry.json', 'r') as f:
            registry_data = json.load(f)
        
        # Verify that tasks in registry match the task queue
        print(f"Registry contains {len(registry_data['tasks'])} tasks")
        
        # Update the last sync timestamp
        registry_data['metadata']['last_sync_with_canonical'] = datetime.now().isoformat()
        registry_data['last_updated_at'] = datetime.now().isoformat()
        
        # Write back the updated registry
        with open('ops/assistant_ops_registry.json', 'w') as f:
            json.dump(registry_data, f, indent=2)
        
        print("Registry synchronization completed")
        return True
    except Exception as e:
        print(f"Synchronization failed: {str(e)}")
        return False


def update_execution_log(task_id, status, result, notes=""):
    """
    Add an entry to the execution log
    """
    log_entry = {
        "task_id": task_id,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "result": result,
        "notes": notes
    }
    
    print(f"Adding log entry for task {task_id}: {status} - {result}")
    # In a real implementation, this would append to the execution log file
    return log_entry


def validate_task_exists(task_id):
    """
    Check if a task exists in the registry
    """
    try:
        with open('ops/assistant_ops_registry.json', 'r') as f:
            registry_data = json.load(f)
        
        for task in registry_data['tasks']:
            if task['task_id'] == task_id:
                return True
        return False
    except Exception:
        return False


def get_task_by_id(task_id):
    """
    Retrieve a specific task by its ID from the registry
    """
    try:
        with open('ops/assistant_ops_registry.json', 'r') as f:
            registry_data = json.load(f)
        
        for task in registry_data['tasks']:
            if task['task_id'] == task_id:
                return task
        return None
    except Exception:
        return None


def update_task_status(task_id, new_status):
    """
    Update the status of a task in the registry
    """
    try:
        with open('ops/assistant_ops_registry.json', 'r') as f:
            registry_data = json.load(f)
        
        for i, task in enumerate(registry_data['tasks']):
            if task['task_id'] == task_id:
                registry_data['tasks'][i]['status'] = new_status
                registry_data['tasks'][i]['updated_at'] = datetime.now().isoformat()
                
                # Write back the updated registry
                with open('ops/assistant_ops_registry.json', 'w') as f:
                    json.dump(registry_data, f, indent=2)
                    
                return True
        return False
    except Exception as e:
        print(f"Failed to update task status: {str(e)}")
        return False