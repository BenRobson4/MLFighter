import json
import os
from typing import Dict, Any, List
from pathlib import Path


class ConfigManager:
    """Manages game configuration from JSON file"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config file in same directory
            config_path = Path(__file__).parent / "game_config.json"
        
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found at {self.config_path}, using defaults")
            return self.get_default_config()
    
    def save_config(self):
        """Save current configuration to JSON file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "token_system": {
                "tokens_per_round": 5,
                "costs": {
                    "unlock_feature": 2,
                    "modify_epsilon": 1,
                    "modify_decay": 1,
                    "modify_learning_rate": 1,
                    "modify_reward_weight": 1
                },
                "modifications": {
                    "epsilon_delta": 0.1,
                    "decay_delta": 0.002,
                    "learning_rate_delta": 0.0005,
                    "reward_weight_delta": 10.0
                }
            },
            "parameter_ranges": {
                "epsilon": {
                    "min": 0.5,
                    "max": 1.0,
                    "initial_min": 0.5,
                    "initial_max": 1.0
                },
                "decay": {
                    "min": 0.990,
                    "max": 0.999,
                    "initial_min": 0.993,
                    "initial_max": 0.998
                },
                "learning_rate": {
                    "min": 0.0001,
                    "max": 0.01,
                    "initial_min": 0.0005,
                    "initial_max": 0.003
                }
            },
            "features": {
                "tier1": [
                    "player_health",
                    "opponent_health", 
                    "distance_x"
                ],
                "tier2": [
                    "player_x", "player_y",
                    "opponent_x", "opponent_y",
                    "player_velocity_x", "player_velocity_y",
                    "opponent_velocity_x", "opponent_velocity_y",
                    "distance_y"
                ]
            },
            "initial_options": {
                "num_options": 3,
                "features_per_option": 3
            }
        }
    
    def get_tokens_for_round(self, round_num: int, player_performance: Dict[str, Any] = None) -> int:
        """
        Calculate tokens for a player based on round and performance.
        Can be extended with more complex logic in the future.
        """
        base_tokens = self.config["token_system"]["tokens_per_round"]
        
        # Future extension point: Add bonus tokens based on performance
        if player_performance:
            # Example: bonus tokens for underdog
            if player_performance.get("win_rate", 0.5) < 0.3:
                base_tokens += 2
            # Example: bonus for improvement
            if player_performance.get("improvement", 0) > 0.1:
                base_tokens += 1
        
        return base_tokens
    
    def get_cost(self, action: str) -> int:
        """Get token cost for an action"""
        return self.config["token_system"]["costs"].get(action, 0)
    
    def get_modification_delta(self, parameter: str) -> float:
        """Get modification amount for a parameter"""
        return self.config["token_system"]["modifications"].get(f"{parameter}_delta", 0)
    
    def get_parameter_range(self, parameter: str) -> Dict[str, float]:
        """Get min/max range for a parameter"""
        return self.config["parameter_ranges"].get(parameter, {})
    
    def get_features_by_tier(self, tier: str) -> List[str]:
        """Get features for a specific tier"""
        return self.config["features"].get(tier, [])