from dataclasses import dataclass
from typing import Dict
import logging

logger = logging.getLogger(__name__)

@dataclass
class LearningParameters:
    """Learning parameters for the ML agent"""
    epsilon: float = 1.0
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    learning_rate: float = 0.001
    
    def apply_modifier(self, modifier_type: str, delta: float):
        """Apply a modifier to a specific parameter"""
        if modifier_type == "epsilon":
            self.epsilon = max(0.0, min(1.0, self.epsilon + delta))
        elif modifier_type == "epsilon_decay":
            self.epsilon_decay = max(0.9, min(0.999, self.epsilon_decay + delta))
        elif modifier_type == "learning_rate":
            self.learning_rate = max(0.0001, min(0.01, self.learning_rate + delta))
        else:
            logger.warning(f"Unknown modifier type: {modifier_type}")
            
    def to_dict(self) -> Dict:
        return {
            "epsilon": self.epsilon,
            "epsilon_decay": self.epsilon_decay,
            "epsilon_min": self.epsilon_min,
            "learning_rate": self.learning_rate
        }