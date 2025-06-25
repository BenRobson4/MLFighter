import json
import logging
from pathlib import Path
from typing import Dict, Optional
from ..data_classes import Fighter, FighterFrameData, ActionFrameData
from ..globals import Action

logger = logging.getLogger(__name__)

class FighterLoader:
    """Loads fighter data from JSON configuration"""
    
    _fighters_cache: Dict[str, Fighter] = {}
    _config_path: Path = None
    
    @classmethod
    def set_config_path(cls, path: Path):
        """Set the path to the fighters configuration file"""
        cls._config_path = path
        cls._fighters_cache.clear()
    
    @classmethod
    def load_fighter(cls, fighter_type: str) -> Fighter:
        """
        Load a fighter by type name
        
        Args:
            fighter_type: Type of fighter (e.g., 'aggressive', 'defensive', 'balanced')
            
        Returns:
            Fighter object with all stats and frame data
            
        Raises:
            ValueError: If fighter type not found
            FileNotFoundError: If config file not found
        """
        # Check cache first
        if fighter_type in cls._fighters_cache:
            return cls._fighters_cache[fighter_type]
        
        # Load from file
        if cls._config_path is None:
            # Default path - adjust based on your project structure
            cls._config_path = Path(__file__).parent.parent / "configs" / "fighters.json"
        
        try:
            with open(cls._config_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Fighters config file not found at {cls._config_path}")
            raise
        
        if fighter_type not in data['fighters']:
            available = list(data['fighters'].keys())
            raise ValueError(f"Fighter type '{fighter_type}' not found. Available: {available}")
        
        fighter_data = data['fighters'][fighter_type]
        
        # Build frame data
        frame_data = cls._build_frame_data(fighter_data.get('frame_data', {}))
        
        # Create fighter
        stats = fighter_data['base_stats']
        fighter = Fighter(
            name=fighter_data['name'],
            gravity=stats['gravity'],
            friction=stats['friction'],
            width=stats['width'],
            height=stats['height'],
            jump_force=stats['jump_force'],
            jump_cooldown=stats['jump_cooldown'],
            move_speed=stats['move_speed'],
            health=stats['health'],
            x_attack_range=stats['x_attack_range'],
            y_attack_range=stats['y_attack_range'],
            attack_damage=stats['attack_damage'],
            attack_cooldown=stats['attack_cooldown'],
            on_hit_stun=stats['on_hit_stun'],
            on_block_stun=stats['on_block_stun'],
            block_efficiency=stats['block_efficiency'],
            block_cooldown=stats['block_cooldown'],
            damage_reduction=stats.get('damage_reduction', 0.0),
            weapon=None,
            armour=None,
            frame_data=frame_data
        )
        
        # Cache the fighter
        cls._fighters_cache[fighter_type] = fighter
        
        logger.info(f"Loaded fighter '{fighter_type}' from config")
        return fighter
    
    @classmethod
    def _build_frame_data(cls, frame_config: Dict) -> FighterFrameData:
        """Build FighterFrameData from JSON configuration"""
        actions = {}
        
        for action_name, frames in frame_config.items():
            try:
                action = Action[action_name]
                actions[action] = ActionFrameData(
                    action=action,
                    startup_frames=frames.get('startup_frames', 0),
                    active_frames=frames.get('active_frames', 0),
                    recovery_frames=frames.get('recovery_frames', 0)
                )
            except KeyError:
                logger.warning(f"Unknown action '{action_name}' in frame data")
                continue
        
        # Ensure all actions have frame data
        for action in Action:
            if action not in actions:
                # Use default frame data for missing actions
                actions[action] = cls._get_default_action_data(action)
        
        return FighterFrameData(actions=actions)
    
    @classmethod
    def _get_default_action_data(cls, action: Action) -> ActionFrameData:
        """Get default frame data for an action"""
        if action == Action.ATTACK:
            return ActionFrameData(action=action, startup_frames=3, active_frames=2, recovery_frames=7)
        elif action == Action.JUMP:
            return ActionFrameData(action=action, startup_frames=2, active_frames=15, recovery_frames=3)
        elif action == Action.BLOCK:
            return ActionFrameData(action=action, startup_frames=2, active_frames=10, recovery_frames=3)
        elif action in [Action.LEFT, Action.RIGHT]:
            return ActionFrameData(action=action, startup_frames=0, active_frames=1, recovery_frames=0)
        else:  # IDLE
            return ActionFrameData(action=action, startup_frames=0, active_frames=1, recovery_frames=0)
    
    @classmethod
    def get_available_fighters(cls) -> Dict[str, str]:
        """
        Get all available fighter types and their descriptions
        
        Returns:
            Dict mapping fighter type to description
        """
        if cls._config_path is None:
            cls._config_path = Path(__file__).parent.parent / "configs" / "fighters.json"
        
        with open(cls._config_path, 'r') as f:
            data = json.load(f)
        
        return {
            fighter_type: fighter_data['description']
            for fighter_type, fighter_data in data['fighters'].items()
        }