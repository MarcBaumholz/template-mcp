"""
Dynamic Task Management MCP Tool
Provides MCP tool interface for the dynamic task management system
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import the task management system
from tools.shared_utilities.dynamic_task_manager import (
    task_manager, 
    update_tasks_after_tool,
    get_task_summary,
    add_manual_task,
    get_next_task
)
from tools.shared_utilities.task_update_templates import TaskUpdateTemplates

def mcp_dynamic_task_management(action: str, **kwargs) -> Dict[str, Any]:
    """
    MCP tool for dynamic task management
    
    Args:
        action: The action to perform
        **kwargs: Additional parameters based on action
    
    Returns:
        Dict with result information
    """
    try:
        if action == "update_after_tool":
            return _update_after_tool(**kwargs)
        elif action == "get_task_summary":
            return _get_task_summary()
        elif action == "add_manual_task":
            return _add_manual_task(**kwargs)
        elif action == "get_next_task":
            return _get_next_task()
        elif action == "get_task_list":
            return _get_task_list()
        elif action == "mark_task_completed":
            return _mark_task_completed(**kwargs)
        elif action == "generate_tasks_from_tool":
            return _generate_tasks_from_tool(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": [
                    "update_after_tool",
                    "get_task_summary", 
                    "add_manual_task",
                    "get_next_task",
                    "get_task_list",
                    "mark_task_completed",
                    "generate_tasks_from_tool"
                ]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "action": action
        }

def _update_after_tool(tool_name: str, output_path: str, analysis: str, new_requirements: List[str] = None) -> Dict[str, Any]:
    """Update tasks after MCP tool execution"""
    try:
        # Generate new requirements if not provided
        if not new_requirements:
            new_requirements = TaskUpdateTemplates.get_tool_specific_requirements(
                tool_name, output_path, analysis
            )
        
        # Update tasks
        update_tasks_after_tool(tool_name, output_path, analysis, new_requirements)
        
        return {
            "success": True,
            "message": f"Tasks updated after {tool_name} execution",
            "tool_name": tool_name,
            "output_path": output_path,
            "new_tasks_generated": len(new_requirements),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update tasks: {str(e)}",
            "tool_name": tool_name
        }

def _get_task_summary() -> Dict[str, Any]:
    """Get current task summary"""
    try:
        summary = get_task_summary()
        return {
            "success": True,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get task summary: {str(e)}"
        }

def _add_manual_task(task_content: str, priority: str = "normal") -> Dict[str, Any]:
    """Add a manual task"""
    try:
        add_manual_task(task_content, priority)
        return {
            "success": True,
            "message": f"Added manual task: {task_content}",
            "task_content": task_content,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add manual task: {str(e)}"
        }

def _get_next_task() -> Dict[str, Any]:
    """Get next task to work on"""
    try:
        next_task = get_next_task()
        if next_task:
            return {
                "success": True,
                "next_task": next_task,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "message": "No tasks available",
                "next_task": None,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get next task: {str(e)}"
        }

def _get_task_list() -> Dict[str, Any]:
    """Get current task list"""
    try:
        tasks = task_manager.load_current_tasks()
        return {
            "success": True,
            "tasks": tasks,
            "total_tasks": len(tasks),
            "completed_tasks": len([t for t in tasks if t.get('completed', False)]),
            "current_tasks": len([t for t in tasks if not t.get('completed', False)]),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get task list: {str(e)}"
        }

def _mark_task_completed(task_id: int) -> Dict[str, Any]:
    """Mark a specific task as completed"""
    try:
        tasks = task_manager.load_current_tasks()
        for task in tasks:
            if task.get('id') == task_id:
                task['completed'] = True
                task['completed_at'] = datetime.now().isoformat()
                task_manager.save_tasks(tasks)
                return {
                    "success": True,
                    "message": f"Marked task {task_id} as completed",
                    "task": task,
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "success": False,
            "error": f"Task {task_id} not found"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to mark task as completed: {str(e)}"
        }

def _generate_tasks_from_tool(tool_name: str, output_path: str, analysis: str) -> Dict[str, Any]:
    """Generate new tasks from tool output without updating task list"""
    try:
        new_requirements = TaskUpdateTemplates.get_tool_specific_requirements(
            tool_name, output_path, analysis
        )
        
        return {
            "success": True,
            "tool_name": tool_name,
            "output_path": output_path,
            "analysis": analysis,
            "new_requirements": new_requirements,
            "count": len(new_requirements),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate tasks: {str(e)}"
        }

# Convenience functions for direct use
def update_tasks_after_mcp_tool(tool_name: str, output_path: str, analysis: str, new_requirements: List[str] = None) -> Dict[str, Any]:
    """Convenience function to update tasks after MCP tool execution"""
    return mcp_dynamic_task_management(
        action="update_after_tool",
        tool_name=tool_name,
        output_path=output_path,
        analysis=analysis,
        new_requirements=new_requirements
    )

def get_mcp_task_summary() -> Dict[str, Any]:
    """Convenience function to get task summary"""
    return mcp_dynamic_task_management(action="get_task_summary")

def add_mcp_manual_task(task_content: str, priority: str = "normal") -> Dict[str, Any]:
    """Convenience function to add manual task"""
    return mcp_dynamic_task_management(
        action="add_manual_task",
        task_content=task_content,
        priority=priority
    )

def get_mcp_next_task() -> Dict[str, Any]:
    """Convenience function to get next task"""
    return mcp_dynamic_task_management(action="get_next_task")
