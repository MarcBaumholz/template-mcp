#!/usr/bin/env python3
"""
Load Predefined Tasks into Dynamic Task Management System
Automatically loads the predefined workflow tasks with customizable placeholders
"""

import sys
import os
import json
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.phase0_bootstrap.dynamic_task_management_tool import mcp_dynamic_task_management

class PredefinedTaskLoader:
    def __init__(self, product_config=None):
        """
        Initialize the predefined task loader
        
        Args:
            product_config: Dict with product-specific configuration
        """
        self.product_config = product_config or {}
        self.default_placeholders = {
            '[PRODUCT_NAME]': 'Generic Product',
            '[SOURCE_API_NAME]': 'Source API',
            '[TARGET_API_NAME]': 'Target API',
            '[BUSINESS_DOMAIN]': 'Business Domain',
            '[INTEGRATION_TYPE]': 'Data Integration',
            '[DATA_FORMAT]': 'JSON',
            '[AUTHENTICATION_TYPE]': 'OAuth 2.0',
            '[FREQUENCY]': 'Real-time'
        }
        
    def replace_placeholders(self, text):
        """Replace placeholders in text with actual values"""
        # Merge default placeholders with product config
        placeholders = {**self.default_placeholders, **self.product_config}
        
        # Replace placeholders
        for placeholder, value in placeholders.items():
            text = text.replace(placeholder, value)
        
        return text
    
    def parse_task_list(self, task_file_path="PREDEFINED_WORKFLOW_TASKS.md"):
        """Parse the predefined task list and extract tasks"""
        try:
            with open(task_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tasks = []
            current_phase = None
            current_section = None
            
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                
                # Detect phase headers
                if line.startswith('## ') and 'Phase' in line:
                    current_phase = line.replace('## ', '').strip()
                    continue
                
                # Detect section headers
                if line.startswith('### ') and not line.startswith('### ' + current_phase):
                    current_section = line.replace('### ', '').strip()
                    continue
                
                # Detect tasks
                if line.startswith('- [ ]'):
                    task_content = line[6:].strip()  # Remove '- [ ] '
                    
                    # Replace placeholders
                    task_content = self.replace_placeholders(task_content)
                    
                    # Determine priority based on phase and content
                    priority = self._determine_priority(current_phase, task_content)
                    
                    # Determine category
                    category = self._determine_category(current_phase, current_section)
                    
                    task = {
                        'content': task_content,
                        'phase': current_phase,
                        'section': current_section,
                        'priority': priority,
                        'category': category,
                        'completed': False
                    }
                    tasks.append(task)
            
            return tasks
            
        except Exception as e:
            print(f"❌ Error parsing task list: {str(e)}")
            return []
    
    def _determine_priority(self, phase, content):
        """Determine task priority based on phase and content"""
        # Critical tasks
        if any(keyword in content.lower() for keyword in [
            'critical', 'must', 'required', 'essential', 'bootstrap', 'environment',
            'upload', 'validate', 'generate', 'test', 'security'
        ]):
            return 'high'
        
        # Important tasks
        elif any(keyword in content.lower() for keyword in [
            'important', 'should', 'documentation', 'optimization', 'monitoring'
        ]):
            return 'medium'
        
        # Optional tasks
        elif any(keyword in content.lower() for keyword in [
            'optional', 'nice to have', 'advanced', 'extended', 'additional'
        ]):
            return 'low'
        
        # Default based on phase
        elif phase and 'Phase 0' in phase:
            return 'high'
        elif phase and 'Phase 1' in phase:
            return 'high'
        elif phase and 'Phase 2' in phase:
            return 'high'
        elif phase and 'Phase 3' in phase:
            return 'high'
        elif phase and 'Phase 4' in phase:
            return 'high'
        else:
            return 'medium'
    
    def _determine_category(self, phase, section):
        """Determine task category based on phase and section"""
        if phase and 'Phase 0' in phase:
            return 'Bootstrap'
        elif phase and 'Phase 1' in phase:
            return 'Data Extraction'
        elif phase and 'Phase 2' in phase:
            return 'Analysis & Mapping'
        elif phase and 'Phase 3' in phase:
            return 'Code Generation'
        elif phase and 'Phase 4' in phase:
            return 'TDD Validation'
        elif phase and 'Phase 5' in phase:
            return 'Learning & Documentation'
        elif phase and 'Phase 6' in phase:
            return 'Maintenance & Optimization'
        else:
            return 'General'
    
    def load_tasks_into_system(self, tasks):
        """Load tasks into the dynamic task management system"""
        loaded_count = 0
        failed_count = 0
        
        print(f"🔄 Loading {len(tasks)} predefined tasks...")
        
        for i, task in enumerate(tasks, 1):
            try:
                result = mcp_dynamic_task_management(
                    action="add_manual_task",
                    task_content=task['content'],
                    priority=task['priority']
                )
                
                if result['success']:
                    loaded_count += 1
                    print(f"✅ {i:3d}. {task['content'][:60]}...")
                else:
                    failed_count += 1
                    print(f"❌ {i:3d}. Failed to load: {task['content'][:60]}...")
                
            except Exception as e:
                failed_count += 1
                print(f"❌ {i:3d}. Error loading task: {str(e)}")
        
        print(f"\n📊 Loading Summary:")
        print(f"   ✅ Successfully loaded: {loaded_count}")
        print(f"   ❌ Failed to load: {failed_count}")
        print(f"   📈 Success rate: {loaded_count/(loaded_count+failed_count)*100:.1f}%")
        
        return loaded_count, failed_count
    
    def generate_task_summary(self, tasks):
        """Generate a summary of loaded tasks"""
        summary = {
            'total_tasks': len(tasks),
            'by_phase': {},
            'by_priority': {},
            'by_category': {}
        }
        
        for task in tasks:
            # Count by phase
            phase = task.get('phase', 'Unknown')
            summary['by_phase'][phase] = summary['by_phase'].get(phase, 0) + 1
            
            # Count by priority
            priority = task.get('priority', 'Unknown')
            summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1
            
            # Count by category
            category = task.get('category', 'Unknown')
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
        
        return summary

def main():
    """Main function to load predefined tasks"""
    print("🚀 Predefined Task Loader")
    print("=" * 50)
    
    # Example product configuration
    product_config = {
        '[PRODUCT_NAME]': 'Absence Management',
        '[SOURCE_API_NAME]': 'Flip HRIS API',
        '[TARGET_API_NAME]': 'Workday API',
        '[BUSINESS_DOMAIN]': 'Human Resources',
        '[INTEGRATION_TYPE]': 'Employee Data Sync',
        '[DATA_FORMAT]': 'JSON',
        '[AUTHENTICATION_TYPE]': 'OAuth 2.0',
        '[FREQUENCY]': 'Real-time'
    }
    
    print("📋 Product Configuration:")
    for key, value in product_config.items():
        print(f"   {key}: {value}")
    
    # Initialize loader
    loader = PredefinedTaskLoader(product_config)
    
    # Parse task list
    print(f"\n📖 Parsing predefined task list...")
    tasks = loader.parse_task_list()
    
    if not tasks:
        print("❌ No tasks found in predefined task list")
        return 1
    
    print(f"✅ Found {len(tasks)} tasks to load")
    
    # Generate summary
    summary = loader.generate_task_summary(tasks)
    print(f"\n📊 Task Summary:")
    print(f"   Total Tasks: {summary['total_tasks']}")
    
    print(f"\n   By Phase:")
    for phase, count in summary['by_phase'].items():
        print(f"     {phase}: {count}")
    
    print(f"\n   By Priority:")
    for priority, count in summary['by_priority'].items():
        print(f"     {priority}: {count}")
    
    print(f"\n   By Category:")
    for category, count in summary['by_category'].items():
        print(f"     {category}: {count}")
    
    # Load tasks into system
    print(f"\n🔄 Loading tasks into dynamic task management system...")
    loaded_count, failed_count = loader.load_tasks_into_system(tasks)
    
    if loaded_count > 0:
        print(f"\n✅ Successfully loaded {loaded_count} predefined tasks!")
        print(f"\n📋 Next Steps:")
        print(f"1. Check TASKS.md for your loaded task list")
        print(f"2. Start with Phase 0 - Bootstrap tasks")
        print(f"3. Use the dynamic task management system to track progress")
        print(f"4. Update task status as you complete each item")
        
        # Show next task
        try:
            result = mcp_dynamic_task_management(action="get_next_task")
            if result['success'] and result['next_task']:
                next_task = result['next_task']
                print(f"\n🎯 Next Task: {next_task['content']}")
        except Exception as e:
            print(f"\n⚠️  Could not get next task: {str(e)}")
    else:
        print(f"\n❌ Failed to load any tasks. Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
