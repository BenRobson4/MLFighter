import random
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any
from ..data_classes import LearningParameters, FighterOption
from ..players import FighterLoader


class FighterOptionGenerator:
    """Generates randomized fighter options for initial selection"""
    
    # Learning parameter ranges for randomization
    PARAM_RANGES = {
        "epsilon": (0.7, 1.0),          # Starting exploration rate
        "epsilon_decay": (0.990, 0.999), # How fast exploration decreases
        "epsilon_min": (0.01, 0.05),     # Minimum exploration
        "learning_rate": (0.0005, 0.005) # How fast the AI learns
    }
    
    # Personality descriptions based on parameters
    LEARNING_STYLES = {
        "aggressive_learner": "Fast learner, takes risks",
        "cautious_learner": "Slow and steady improvement",
        "explorer": "Tries many strategies",
        "exploiter": "Quickly settles on a strategy"
    }
    
    @classmethod
    def generate_fighter_options(cls, num_options: int = 3, num_features: int = 20) -> List[FighterOption]:
        """Generate randomized fighter options"""
        # Get available fighter types
        available_fighters = FighterLoader.get_available_fighters()
        fighter_list = list(available_fighters.keys())
        # Randomly select fighters (with replacement if needed)
        if len(available_fighters) >= num_options:
            selected_fighters = random.sample(fighter_list, num_options)
        else:
            selected_fighters = random.choices(fighter_list, k=num_options)
        
        options = []
        for i, fighter_name in enumerate(selected_fighters):
            # Generate randomized learning parameters
            learning_params = cls._generate_random_learning_params()

            # Generate randomized feature mask
            feature_mask = cls._generate_random_feature_mask(num_features)
            
            # Create description based on parameters
            description = cls._describe_learning_style(learning_params, feature_mask, fighter_name)
            
            option = FighterOption(
                option_id=f"fighter_option_{i}",
                fighter_name=fighter_name,
                learning_parameters=learning_params,
                initial_feature_mask=feature_mask,
                description=description
            )
            options.append(option)
        
        return options
    
    @classmethod
    def _generate_random_learning_params(cls) -> LearningParameters:
        """Generate randomized learning parameters"""
        return LearningParameters(
            epsilon=random.uniform(*cls.PARAM_RANGES["epsilon"]),
            epsilon_decay=random.uniform(*cls.PARAM_RANGES["epsilon_decay"]),
            epsilon_min=0.025,  # Fixed minimum exploration
            learning_rate=random.uniform(*cls.PARAM_RANGES["learning_rate"])
        )
    
    @classmethod
    def _generate_random_feature_mask(cls, num_features: int) -> np.ndarray:
        """Generate a random feature mask with varying complexity"""
        mask = np.zeros(num_features)
        
        # Basic features
        basic_features = [0, 1, 2, 9, 10, 11]  # P1.x, P1.y, P1.health, P2.x, P2.y, P2.health
        chosen_features = random.sample(basic_features, 4)

        for idx in chosen_features:
            mask[idx] = 1
        
        return mask

    @classmethod
    def _describe_learning_style(cls, params: LearningParameters, feature_mask: np.ndarray, fighter_name: str) -> str:
        """Generate a description based on the learning parameters"""
        style_parts = []
        
        # Describe exploration tendency
        if params.epsilon > 0.95:
            style_parts.append("Highly experimental")
        elif params.epsilon < 0.85:
            style_parts.append("Focused approach")
        
        # Describe learning speed
        if params.learning_rate > 0.003:
            style_parts.append("quick to adapt")
        elif params.learning_rate < 0.001:
            style_parts.append("steady learner")
        
        # Describe decay rate
        if params.epsilon_decay > 0.997:
            style_parts.append("maintains flexibility")
        elif params.epsilon_decay < 0.993:
            style_parts.append("rapidly specializes")
        
        # Include parameters
        if feature_mask[0] == 1:
            style_parts.append("includes feature P1.x")
        if feature_mask[1] == 1:
            style_parts.append("includes feature P1.y")
        if feature_mask[2] == 1:
            style_parts.append("includes feature P1.health")
        if feature_mask[9] == 1:
            style_parts.append("includes feature P2.x")
        if feature_mask[10] == 1:
            style_parts.append("includes feature P2.y")
        if feature_mask[11] == 1:
            style_parts.append("includes feature P2.health")
        
        style_desc = ", ".join(style_parts) if style_parts else "Balanced learning style"
        return f"{fighter_name.title()} fighter - {style_desc}"