"""
Dynamic Task Management System
Updates task list after each MCP tool execution based on tool outputs and new information
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class DynamicTaskManager:
    def __init__(self, task_file_path: str = "TASKS.md", status_file_path: str = "STATUS.md"):
        self.task_file_path = task_file_path
        self.status_file_path = status_file_path
        self.current_tasks = []
        self.completed_tasks = []
        self.new_tasks = []
        self.task_counter = 0
        
    def load_current_tasks(self) -> List[Dict[str, Any]]:
        """Load current tasks from TASKS.md file"""
        if not os.path.exists(self.task_file_path):
            return []
        
        try:
            with open(self.task_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse markdown task list
            tasks = []
            lines = content.split('\n')
            current_task = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('- [ ]') or line.startswith('- [x]'):
                    # Extract task content
                    task_content = line[6:].strip()  # Remove '- [ ] ' or '- [x] '
                    is_completed = line.startswith('- [x]')
                    
                    task = {
                        'id': len(tasks) + 1,
                        'content': task_content,
                        'completed': is_completed,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    tasks.append(task)
            
            return tasks
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return []
    
    def save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """Save tasks to TASKS.md file"""
        try:
            with open(self.task_file_path, 'w', encoding='utf-8') as f:
                f.write("# 🎯 Dynamic Task Management System\n\n")
                f.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Completed tasks
                completed = [t for t in tasks if t.get('completed', False)]
                if completed:
                    f.write("## ✅ Completed Tasks\n\n")
                    for task in completed:
                        f.write(f"- [x] {task['content']}\n")
                    f.write("\n")
                
                # Current tasks
                current = [t for t in tasks if not t.get('completed', False)]
                if current:
                    f.write("## 🔄 Current Tasks\n\n")
                    for task in current:
                        f.write(f"- [ ] {task['content']}\n")
                    f.write("\n")
                
                # New tasks
                if self.new_tasks:
                    f.write("## 🆕 New Tasks Generated\n\n")
                    for task in self.new_tasks:
                        f.write(f"- [ ] {task['content']}\n")
                    f.write("\n")
                
                # Task statistics
                f.write("## 📊 Task Statistics\n\n")
                f.write(f"- **Total Tasks:** {len(tasks)}\n")
                f.write(f"- **Completed:** {len(completed)}\n")
                f.write(f"- **Current:** {len(current)}\n")
                f.write(f"- **New:** {len(self.new_tasks)}\n")
                
        except Exception as e:
            print(f"Error saving tasks: {e}")
    
    def update_after_tool_execution(self, tool_name: str, output_path: str, analysis: str, new_requirements: List[str] = None) -> None:
        """Update task list after MCP tool execution"""
        print(f"🔄 Updating tasks after {tool_name} execution...")
        
        # Load current tasks
        self.current_tasks = self.load_current_tasks()
        
        # Mark current task as completed if it matches the tool
        self._mark_task_completed(tool_name)
        
        # Generate new tasks based on tool output
        if new_requirements:
            self._generate_new_tasks(new_requirements, tool_name, output_path)
        
        # Update task priorities and renumber
        self._update_task_priorities()
        
        # Save updated tasks
        self.save_tasks(self.current_tasks)
        
        # Update status file
        self._update_status_file(tool_name, output_path, analysis)
        
        print(f"✅ Tasks updated successfully. Generated {len(self.new_tasks)} new tasks.")
    
    def _mark_task_completed(self, tool_name: str) -> None:
        """Mark the current task as completed"""
        for task in self.current_tasks:
            if not task.get('completed', False):
                # Check if task content matches tool name or contains tool reference
                if (tool_name.lower() in task['content'].lower() or 
                    any(keyword in task['content'].lower() for keyword in ['upload', 'analyze', 'generate', 'map', 'validate'])):
                    task['completed'] = True
                    task['completed_at'] = datetime.now().isoformat()
                    print(f"✅ Marked task as completed: {task['content']}")
                    break
    
    def _generate_new_tasks(self, new_requirements: List[str], tool_name: str, output_path: str) -> None:
        """Generate new tasks based on tool output and new requirements"""
        self.new_tasks = []
        
        for requirement in new_requirements:
            new_task = {
                'id': len(self.current_tasks) + len(self.new_tasks) + 1,
                'content': requirement,
                'completed': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'source_tool': tool_name,
                'source_output': output_path
            }
            self.new_tasks.append(new_task)
            self.current_tasks.append(new_task)
        
        print(f"🆕 Generated {len(self.new_tasks)} new tasks from {tool_name} output")
    
    def _update_task_priorities(self) -> None:
        """Update task priorities and renumber tasks"""
        # Renumber all tasks
        for i, task in enumerate(self.current_tasks):
            task['id'] = i + 1
            task['updated_at'] = datetime.now().isoformat()
        
        # Sort by priority (current tasks first, then new tasks)
        self.current_tasks.sort(key=lambda x: (x.get('completed', False), x.get('id', 0)))
    
    def _update_status_file(self, tool_name: str, output_path: str, analysis: str) -> None:
        """Update STATUS.md file with latest tool execution info"""
        try:
            status_content = f"""# 📊 Workflow Status Dashboard

## 🔄 Last Tool Execution
- **Tool:** {tool_name}
- **Output:** {output_path}
- **Analysis:** {analysis}
- **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 Task Progress
- **Total Tasks:** {len(self.current_tasks)}
- **Completed:** {len([t for t in self.current_tasks if t.get('completed', False)])}
- **Current:** {len([t for t in self.current_tasks if not t.get('completed', False)])}
- **New Generated:** {len(self.new_tasks)}

## 🎯 Next Actions
Based on the latest tool execution, the following actions are recommended:
"""
            
            # Add next actions based on tool output
            if 'upload' in tool_name.lower():
                status_content += "\n- Review uploaded data and validate structure"
                status_content += "\n- Proceed with analysis and mapping"
            elif 'analyze' in tool_name.lower():
                status_content += "\n- Review analysis results and identify gaps"
                status_content += "\n- Generate mapping recommendations"
            elif 'generate' in tool_name.lower():
                status_content += "\n- Review generated code and run quality checks"
                status_content += "\n- Execute validation tests"
            elif 'validate' in tool_name.lower():
                status_content += "\n- Review validation results and fix issues"
                status_content += "\n- Proceed to next phase if validation passes"
            
            with open(self.status_file_path, 'w', encoding='utf-8') as f:
                f.write(status_content)
                
        except Exception as e:
            print(f"Error updating status file: {e}")
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Get current task summary"""
        completed = [t for t in self.current_tasks if t.get('completed', False)]
        current = [t for t in self.current_tasks if not t.get('completed', False)]
        
        return {
            'total_tasks': len(self.current_tasks),
            'completed_tasks': len(completed),
            'current_tasks': len(current),
            'new_tasks': len(self.new_tasks),
            'completion_rate': len(completed) / len(self.current_tasks) if self.current_tasks else 0
        }
    
    def add_manual_task(self, task_content: str, priority: str = "normal") -> None:
        """Add a manual task to the list"""
        new_task = {
            'id': len(self.current_tasks) + 1,
            'content': task_content,
            'completed': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'priority': priority,
            'manual': True
        }
        self.current_tasks.append(new_task)
        self.save_tasks(self.current_tasks)
        print(f"✅ Added manual task: {task_content}")
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next uncompleted task"""
        for task in self.current_tasks:
            if not task.get('completed', False):
                return task
        return None

# Global task manager instance
task_manager = DynamicTaskManager()

def update_tasks_after_tool(tool_name: str, output_path: str, analysis: str, new_requirements: List[str] = None):
    """Convenience function to update tasks after tool execution"""
    task_manager.update_after_tool_execution(tool_name, output_path, analysis, new_requirements)

def get_task_summary():
    """Get current task summary"""
    return task_manager.get_task_summary()

def add_manual_task(task_content: str, priority: str = "normal"):
    """Add a manual task"""
    task_manager.add_manual_task(task_content, priority)

def get_next_task():
    """Get next task to work on"""
    return task_manager.get_next_task()
