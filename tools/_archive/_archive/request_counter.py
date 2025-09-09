"""
Request Counter for AI API Usage Tracking
Tracks how many requests each tool makes to AI services
"""

import json
import os
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
import threading

class RequestCounter:
    """Thread-safe request counter for tracking AI API usage"""
    
    def __init__(self, log_file: str = "ai_request_log.json"):
        self.log_file = log_file
        self.lock = threading.Lock()
        self._load_counts()
    
    def _load_counts(self):
        """Load existing counts from file"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {
                    "total_requests": 0,
                    "requests_by_tool": {},
                    "requests_by_model": {},
                    "daily_counts": {},
                    "session_start": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Warning: Could not load request counts: {e}")
            self.data = {
                "total_requests": 0,
                "requests_by_tool": {},
                "requests_by_model": {},
                "daily_counts": {},
                "session_start": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_counts(self):
        """Save counts to file"""
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            with open(self.log_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save request counts: {e}")
    
    def increment(self, tool_name: str, model_name: str = "unknown", tokens_used: int = 0):
        """Increment request count for a tool"""
        with self.lock:
            # Update total
            self.data["total_requests"] += 1
            
            # Update by tool
            if tool_name not in self.data["requests_by_tool"]:
                self.data["requests_by_tool"][tool_name] = {
                    "count": 0,
                    "tokens": 0,
                    "first_request": datetime.now().isoformat(),
                    "last_request": datetime.now().isoformat()
                }
            
            self.data["requests_by_tool"][tool_name]["count"] += 1
            self.data["requests_by_tool"][tool_name]["tokens"] += tokens_used
            self.data["requests_by_tool"][tool_name]["last_request"] = datetime.now().isoformat()
            
            # Update by model
            if model_name not in self.data["requests_by_model"]:
                self.data["requests_by_model"][model_name] = {
                    "count": 0,
                    "tokens": 0
                }
            
            self.data["requests_by_model"][model_name]["count"] += 1
            self.data["requests_by_model"][model_name]["tokens"] += tokens_used
            
            # Update daily counts
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self.data["daily_counts"]:
                self.data["daily_counts"][today] = 0
            self.data["daily_counts"][today] += 1
            
            # Save to file
            self._save_counts()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        with self.lock:
            return {
                "total_requests": self.data["total_requests"],
                "tools_used": len(self.data["requests_by_tool"]),
                "models_used": len(self.data["requests_by_model"]),
                "session_start": self.data["session_start"],
                "last_updated": self.data["last_updated"],
                "top_tools": sorted(
                    [(k, v["count"]) for k, v in self.data["requests_by_tool"].items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "top_models": sorted(
                    [(k, v["count"]) for k, v in self.data["requests_by_model"].items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            }
    
    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get statistics for a specific tool"""
        with self.lock:
            if tool_name in self.data["requests_by_tool"]:
                return self.data["requests_by_tool"][tool_name]
            return {"count": 0, "tokens": 0}
    
    def reset_counts(self):
        """Reset all counts"""
        with self.lock:
            self.data = {
                "total_requests": 0,
                "requests_by_tool": {},
                "requests_by_model": {},
                "daily_counts": {},
                "session_start": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            self._save_counts()
    
    def print_stats(self):
        """Print current statistics"""
        stats = self.get_stats()
        print("🔢 AI Request Counter Statistics")
        print("=" * 40)
        print(f"📊 Total Requests: {stats['total_requests']}")
        print(f"🛠️  Tools Used: {stats['tools_used']}")
        print(f"🤖 Models Used: {stats['models_used']}")
        print(f"⏰ Session Start: {stats['session_start']}")
        print(f"🔄 Last Updated: {stats['last_updated']}")
        
        if stats['top_tools']:
            print("\n🏆 Top Tools by Usage:")
            for tool, count in stats['top_tools']:
                print(f"   • {tool}: {count} requests")
        
        if stats['top_models']:
            print("\n🤖 Top Models by Usage:")
            for model, count in stats['top_models']:
                print(f"   • {model}: {count} requests")

# Global instance
_request_counter = None

def get_request_counter() -> RequestCounter:
    """Get global request counter instance"""
    global _request_counter
    if _request_counter is None:
        _request_counter = RequestCounter()
    return _request_counter

def track_request(tool_name: str, model_name: str = "unknown", tokens_used: int = 0):
    """Convenience function to track a request"""
    counter = get_request_counter()
    counter.increment(tool_name, model_name, tokens_used)
    print(f"📈 Request tracked: {tool_name} ({model_name}) - Total: {counter.get_stats()['total_requests']}")

def print_usage_stats():
    """Convenience function to print usage statistics"""
    counter = get_request_counter()
    counter.print_stats()

# Decorator for tracking function calls
def track_ai_requests(tool_name: str, model_name: str = "unknown"):
    """Decorator to automatically track AI requests"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                track_request(tool_name, model_name)
                return result
            except Exception as e:
                # Still track even if there's an error
                track_request(tool_name, model_name)
                raise e
        return wrapper
    return decorator


