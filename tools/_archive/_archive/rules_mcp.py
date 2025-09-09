#!/usr/bin/env python3
"""
Rules MCP Tool - Copies .cursor/rules folder to current working directory
Simple tool to bootstrap development environment with all rules and guidelines
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

def _get_source_rules_dir() -> Path:
    """Get the source rules directory path."""
    return Path(__file__).parent.parent / ".cursor" / "rules"

def _copy_recursive(src: Path, dst: Path, base_src: Path) -> Tuple[List[str], List[str]]:
    """Recursively copy directory structure and return copied items."""
    copied_files, copied_dirs = [], []
    
    if src.is_file():
        shutil.copy2(src, dst)
        copied_files.append(str(src.relative_to(base_src)))
    elif src.is_dir():
        dst.mkdir(exist_ok=True)
        copied_dirs.append(str(src.relative_to(base_src)))
        for item in src.iterdir():
            files, dirs = _copy_recursive(item, dst / item.name, base_src)
            copied_files.extend(files)
            copied_dirs.extend(dirs)
    
    return copied_files, copied_dirs

def _generate_summary(target_dir: Path, files: List[str], dirs: List[str]) -> str:
    """Generate copy operation summary."""
    return f"""✅ Rules successfully copied to: {target_dir}

📊 Copy Summary:
- Files copied: {len(files)}
- Directories copied: {len(dirs)}
- Total items: {len(files) + len(dirs)}

📁 Copied Files:
{chr(10).join(f"  • {f}" for f in sorted(files))}

📂 Copied Directories:
{chr(10).join(f"  • {d}" for d in sorted(dirs))}

🚀 Next Steps:
1. Your development environment now has all the rules and guidelines
2. You can start using the MCP tools with full context
3. The .cursor/rules folder contains all necessary configuration

💡 Usage:
- All MCP tools will now have access to the complete rule set
- Cognitive-Mind orchestration is ready to use
- Mapping rules and guidelines are available for API integration workflows"""

def copy_rules_to_working_directory(target_directory: Optional[str] = None) -> str:
    """
    Copy the entire .cursor/rules folder structure to the current working directory.
    
    Args:
        target_directory: Optional target directory (defaults to current working directory)
    
    Returns:
        Status message with details about the copy operation
    """
    try:
        source_rules_dir = _get_source_rules_dir()
        if not source_rules_dir.exists():
            return f"❌ Error: Source rules directory not found at {source_rules_dir}"
        
        target_dir = Path(target_directory) if target_directory else Path.cwd()
        target_rules_dir = target_dir / ".cursor" / "rules"
        target_rules_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy all items recursively
        all_files, all_dirs = [], []
        for item in source_rules_dir.iterdir():
            files, dirs = _copy_recursive(item, target_rules_dir / item.name, source_rules_dir)
            all_files.extend(files)
            all_dirs.extend(dirs)
        
        summary = _generate_summary(target_rules_dir, all_files, all_dirs)
        logger.info(f"Rules copied successfully to {target_rules_dir}")
        return summary
        
    except Exception as e:
        error_msg = f"❌ Error copying rules: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_rules_source_info() -> str:
    """
    Get information about the source rules directory.
    
    Returns:
        Information about the current rules structure
    """
    try:
        source_rules_dir = _get_source_rules_dir()
        if not source_rules_dir.exists():
            return "❌ Source rules directory not found"
        
        # Count files, directories, and total size
        file_count = dir_count = total_size = 0
        structure = []
        
        for item in sorted(source_rules_dir.rglob("*")):
            if item.is_file():
                file_count += 1
                total_size += item.stat().st_size
                structure.append(f"  📄 {item.relative_to(source_rules_dir)}")
            elif item.is_dir() and item != source_rules_dir:
                dir_count += 1
                structure.append(f"  📁 {item.relative_to(source_rules_dir)}/")
        
        return f"""📋 Rules Source Information

📍 Source Location: {source_rules_dir}
📊 Statistics:
  • Files: {file_count}
  • Directories: {dir_count}
  • Total Size: {total_size / 1024:.1f} KB

📂 Structure:
{chr(10).join(structure)}

💡 This is what will be copied to your working directory"""
        
    except Exception as e:
        return f"❌ Error getting rules info: {str(e)}"
