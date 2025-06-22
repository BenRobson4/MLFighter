from typing import Dict, List, Type, Optional
import importlib
import os
import glob
from ...data_classes import Fighter


class FighterRegistry:
    """Registry for all available fighters"""
    
    _fighters: Dict[str, Type[Fighter]] = {}
    
    @classmethod
    def register(cls, fighter_class: Type[Fighter]):
        """Register a fighter class"""
        cls._fighters[fighter_class.__name__] = fighter_class
        return fighter_class
    
    @classmethod
    def get_fighter(cls, name: str) -> Optional[Type[Fighter]]:
        """Get fighter class by name"""
        return cls._fighters.get(name)
    
    @classmethod
    def list_fighters(cls) -> List[str]:
        """List all registered fighter names"""
        return list(cls._fighters.keys())
    
    @classmethod
    def auto_discover(cls, directory: str = 'fighters/types'):
        """Auto-discover fighters from Python files in directory"""
        module_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), directory)
        
        for file_path in glob.glob(os.path.join(module_dir, '*.py')):
            if os.path.basename(file_path) in ['__init__.py', 'fighter.py']:
                continue
                
            rel_path = os.path.relpath(file_path, os.path.dirname(os.path.dirname(module_dir)))
            module_path = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
            
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                print(f"Failed to import {module_path}: {e}")

