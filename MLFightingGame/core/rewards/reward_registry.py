from typing import Dict, List, Type, Optional
import importlib
import os
import glob
from .base_reward import RewardEvent


class RewardRegistry:
    """Registry for all available reward events"""
    
    _events: Dict[str, Type[RewardEvent]] = {}
    
    @classmethod
    def register(cls, event_class: Type[RewardEvent]):
        """Register a reward event class"""
        cls._events[event_class().__class__.__name__] = event_class
        return event_class
    
    @classmethod
    def get_event(cls, event_name: str) -> Optional[Type[RewardEvent]]:
        """Get reward event class by name"""
        return cls._events.get(event_name)
    
    @classmethod
    def list_events(cls) -> List[str]:
        """List all registered event names"""
        return list(cls._events.keys())
    
    @classmethod
    def get_all_events(cls) -> Dict[str, Type[RewardEvent]]:
        """Get all registered events"""
        return cls._events.copy()
    
    @classmethod
    def auto_discover(cls, directory: str = 'rewards/events'):
        """Auto-discover reward events from Python files in directory"""
        # Get absolute path to the directory
        module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), directory)
        
        # Find all Python files in the directory
        for file_path in glob.glob(os.path.join(module_dir, '*.py')):
            if os.path.basename(file_path) in ['__init__.py', 'base_reward.py']:
                continue
                
            # Convert file path to module path
            rel_path = os.path.relpath(file_path, os.path.dirname(os.path.dirname(module_dir)))
            module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
            
            # Import the module
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                print(f"Failed to import {module_path}: {e}")
