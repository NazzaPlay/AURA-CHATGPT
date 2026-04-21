"""
Operational Supervisor Helper Module
This module exposes the operational supervisor helper functions for external use
"""

from .initializer import (
    initialize_operational_supervisor,
    sync_registries,
    update_execution_log,
    validate_task_exists,
    get_task_by_id,
    update_task_status
)

__all__ = [
    'initialize_operational_supervisor',
    'sync_registries', 
    'update_execution_log',
    'validate_task_exists',
    'get_task_by_id',
    'update_task_status'
]

# Example usage:
if __name__ == "__main__":
    print("Operational Supervisor Helper ready")
    print("Available functions:")
    print("- initialize_operational_supervisor()")
    print("- sync_registries()")
    print("- update_execution_log(task_id, status, result, notes)")
    print("- validate_task_exists(task_id)")
    print("- get_task_by_id(task_id)")
    print("- update_task_status(task_id, new_status)")
    
    # Quick validation that all functions are accessible
    print("\nValidating helper availability...")
    functions = [
        initialize_operational_supervisor,
        sync_registries,
        update_execution_log,
        validate_task_exists,
        get_task_by_id,
        update_task_status
    ]
    
    for func in functions:
        print(f"- {func.__name__} is available")
    
    print("\nHelper module validated successfully!")