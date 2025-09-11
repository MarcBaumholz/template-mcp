#!/usr/bin/env python3
"""
Load Improved Predefined Tasks into Dynamic Task Management System
Automatically loads the improved predefined workflow tasks with precise MCP tool sequences
"""

import sys
import os
import json
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.phase0_bootstrap.dynamic_task_management_tool import mcp_dynamic_task_management

class ImprovedPredefinedTaskLoader:
    def __init__(self, product_config=None):
        """
        Initialize the improved predefined task loader
        
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
        
        # MCP tool mapping for better task categorization
        self.mcp_tools = {
            'test_rag_system': 'Phase 0 - Bootstrap',
            'copy_rules_to_working_directory': 'Phase 0 - Bootstrap',
            'get_rules_source_info': 'Phase 0 - Bootstrap',
            'upload_api_specification': 'Phase 1 - Data Extraction',
            'analyze_json_fields_with_rag': 'Phase 1 - Data Extraction',
            'list_available_api_specs': 'Phase 1 - Data Extraction',
            'query_api_specification': 'Phase 2 - Analysis & Mapping',
            'get_direct_api_mapping_prompt': 'Phase 2 - Analysis & Mapping',
            'enhanced_rag_analysis': 'Phase 2 - Analysis & Mapping',
            'reasoning_agent': 'Phase 2 - Analysis & Mapping',
            'iterative_mapping_with_feedback': 'Phase 2 - Analysis & Mapping',
            'generate_kotlin_mapping_code': 'Phase 3 - Code Generation',
            'phase3_generate_mapper': 'Phase 3 - Code Generation',
            'phase3_quality_suite': 'Phase 3 - Code Generation',
            'phase3_select_best_candidate': 'Phase 3 - Code Generation',
            'phase4_tdd_validation': 'Phase 4 - TDD Validation',
            'persist_phase_learnings': 'Phase 5 - Learning & Documentation'
        }
        
    def replace_placeholders(self, text):
        """Replace placeholders in text with actual values"""
        # Merge default placeholders with product config
        placeholders = {**self.default_placeholders, **self.product_config}
        
        # Replace placeholders
        for placeholder, value in placeholders.items():
            text = text.replace(placeholder, value)
        
        return text
    
    def extract_mcp_tool_from_task(self, task_content):
        """Extract MCP tool name from task content"""
        for tool_name in self.mcp_tools.keys():
            if tool_name in task_content:
                return tool_name
        return None
    
    def parse_improved_task_list(self, task_file_path="PREDEFINED_WORKFLOW_TASKS_IMPROVED.md"):
        """Parse the improved predefined task list and extract tasks"""
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
                    
                    # Extract MCP tool if present
                    mcp_tool = self.extract_mcp_tool_from_task(task_content)
                    
                    # Determine priority based on phase and content
                    priority = self._determine_priority(current_phase, task_content, mcp_tool)
                    
                    # Determine category
                    category = self._determine_category(current_phase, current_section)
                    
                    # Determine task type
                    task_type = self._determine_task_type(task_content, mcp_tool)
                    
                    task = {
                        'content': task_content,
                        'phase': current_phase,
                        'section': current_section,
                        'priority': priority,
                        'category': category,
                        'mcp_tool': mcp_tool,
                        'task_type': task_type,
                        'completed': False
                    }
                    tasks.append(task)
            
            return tasks
            
        except Exception as e:
            print(f"❌ Error parsing improved task list: {str(e)}")
            return []
    
    def _determine_priority(self, phase, content, mcp_tool):
        """Determine task priority based on phase, content, and MCP tool"""
        # Critical MCP tools
        critical_tools = [
            'test_rag_system', 'upload_api_specification', 'query_api_specification',
            'reasoning_agent', 'phase3_generate_mapper', 'phase4_tdd_validation'
        ]
        
        if mcp_tool and mcp_tool in critical_tools:
            return 'high'
        
        # Critical keywords
        if any(keyword in content.lower() for keyword in [
            'critical', 'must', 'required', 'essential', 'bootstrap', 'environment',
            'upload', 'validate', 'generate', 'test', 'security', 'human approval'
        ]):
            return 'high'
        
        # Important keywords
        elif any(keyword in content.lower() for keyword in [
            'important', 'should', 'documentation', 'optimization', 'monitoring',
            'save', 'document', 'review'
        ]):
            return 'medium'
        
        # Default based on phase
        elif phase and any(phase_num in phase for phase_num in ['Phase 0', 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4']):
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
    
    def _determine_task_type(self, content, mcp_tool):
        """Determine task type based on content and MCP tool"""
        if mcp_tool:
            return f'MCP Tool: {mcp_tool}'
        elif 'save' in content.lower() or 'document' in content.lower():
            return 'Documentation'
        elif 'review' in content.lower() or 'validate' in content.lower():
            return 'Validation'
        elif 'generate' in content.lower() or 'create' in content.lower():
            return 'Generation'
        elif 'test' in content.lower() or 'execute' in content.lower():
            return 'Testing'
        else:
            return 'General'
    
    def load_tasks_into_system(self, tasks):
        """Load tasks into the dynamic task management system"""
        loaded_count = 0
        failed_count = 0
        
        print(f"🔄 Loading {len(tasks)} improved predefined tasks...")
        
        for i, task in enumerate(tasks, 1):
            try:
                result = mcp_dynamic_task_management(
                    action="add_manual_task",
                    task_content=task['content'],
                    priority=task['priority']
                )
                
                if result['success']:
                    loaded_count += 1
                    status_icon = "🔧" if task['mcp_tool'] else "📋"
                    print(f"✅ {i:3d}. {status_icon} {task['content'][:60]}...")
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
    
    def generate_detailed_summary(self, tasks):
        """Generate a detailed summary of loaded tasks"""
        summary = {
            'total_tasks': len(tasks),
            'by_phase': {},
            'by_priority': {},
            'by_category': {},
            'by_mcp_tool': {},
            'by_task_type': {}
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
            
            # Count by MCP tool
            mcp_tool = task.get('mcp_tool', 'No MCP Tool')
            summary['by_mcp_tool'][mcp_tool] = summary['by_mcp_tool'].get(mcp_tool, 0) + 1
            
            # Count by task type
            task_type = task.get('task_type', 'Unknown')
            summary['by_task_type'][task_type] = summary['by_task_type'].get(task_type, 0) + 1
        
        return summary
    
    def print_workflow_sequence(self, tasks):
        """Print the MCP tool workflow sequence"""
        print(f"\n🔧 MCP Tool Workflow Sequence:")
        print(f"=" * 60)
        
        mcp_tool_sequence = []
        for task in tasks:
            if task.get('mcp_tool'):
                mcp_tool_sequence.append({
                    'tool': task['mcp_tool'],
                    'phase': task.get('phase', 'Unknown'),
                    'section': task.get('section', 'Unknown'),
                    'content': task['content']
                })
        
        # Group by phase
        current_phase = None
        for item in mcp_tool_sequence:
            if item['phase'] != current_phase:
                current_phase = item['phase']
                print(f"\n📋 {current_phase}:")
            print(f"   🔧 {item['tool']} - {item['content'][:50]}...")

def main():
    """Main function to load improved predefined tasks"""
    print("🚀 Improved Predefined Task Loader")
    print("=" * 60)
    
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
    loader = ImprovedPredefinedTaskLoader(product_config)
    
    # Parse improved task list
    print(f"\n📖 Parsing improved predefined task list...")
    tasks = loader.parse_improved_task_list()
    
    if not tasks:
        print("❌ No tasks found in improved predefined task list")
        return 1
    
    print(f"✅ Found {len(tasks)} tasks to load")
    
    # Generate detailed summary
    summary = loader.generate_detailed_summary(tasks)
    print(f"\n📊 Detailed Task Summary:")
    print(f"   Total Tasks: {summary['total_tasks']}")
    
    print(f"\n   By Phase:")
    for phase, count in summary['by_phase'].items():
        print(f"     {phase}: {count}")
    
    print(f"\n   By Priority:")
    for priority, count in summary['by_priority'].items():
        print(f"     {priority}: {count}")
    
    print(f"\n   By MCP Tool:")
    for tool, count in summary['by_mcp_tool'].items():
        if tool != 'No MCP Tool':
            print(f"     {tool}: {count}")
    
    print(f"\n   By Task Type:")
    for task_type, count in summary['by_task_type'].items():
        print(f"     {task_type}: {count}")
    
    # Print workflow sequence
    loader.print_workflow_sequence(tasks)
    
    # Load tasks into system
    print(f"\n🔄 Loading tasks into dynamic task management system...")
    loaded_count, failed_count = loader.load_tasks_into_system(tasks)
    
    if loaded_count > 0:
        print(f"\n✅ Successfully loaded {loaded_count} improved predefined tasks!")
        print(f"\n📋 Next Steps:")
        print(f"1. Check TASKS.md for your loaded task list")
        print(f"2. Start with Phase 0 - Bootstrap tasks")
        print(f"3. Follow the precise MCP tool sequence in each phase")
        print(f"4. Use the dynamic task management system to track progress")
        print(f"5. Update task status as you complete each item")
        
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
