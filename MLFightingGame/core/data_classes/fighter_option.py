from dataclasses import dataclass
import numpy as np
from typing import Dict, Any
from .learning_parameters import LearningParameters

@dataclass
class FighterOption:
    """Represents a fighter choice with randomized learning parameters"""
    option_id: str
    fighter_name: str
    learning_parameters: LearningParameters
    initial_feature_mask: np.ndarray 
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "option_id": self.option_id,
            "fighter_name": self.fighter_name,
            "learning_parameters": self.learning_parameters.to_dict(),
            "initial_feature_mask": self.initial_feature_mask.tolist(),
            "active_features": int(sum(self.initial_feature_mask)),
            "description": self.description
        }