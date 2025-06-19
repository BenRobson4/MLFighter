from dataclasses import dataclass, field
from typing import List, Set
import torch

@dataclass
class AgentConfig:
    """Configuration for DQN Agent"""
    # Feature selection
    included_features: Set[str] = field(default_factory=lambda: {
        'player_x', 'player_y', 'player_health', 'player_velocity_x', 'player_velocity_y',
        'player_is_jumping', 'player_is_blocking', 'player_is_attacking', 'player_attack_cooldown',
        'opponent_x', 'opponent_y', 'opponent_health', 'opponent_velocity_x', 'opponent_velocity_y',
        'opponent_is_jumping', 'opponent_is_blocking', 'opponent_is_attacking', 'opponent_attack_cooldown',
        'distance_x', 'distance_y'
    })
    
    # Network architecture
    hidden_layers: List[int] = field(default_factory=lambda: [128, 64])
    activation: str = 'relu'  # 'relu', 'tanh', 'sigmoid'
    dropout_rate: float = 0.0
    
    # Learning parameters
    learning_rate: float = 0.001
    gamma: float = 0.99  # Discount factor
    epsilon_start: float = 1.0  # Exploration rate
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    
    # Experience replay
    memory_size: int = 10000
    batch_size: int = 32
    update_frequency: int = 4  # Update network every N steps
    target_update_frequency: int = 100  # Update target network every N steps
    
    # Training settings
    use_double_dqn: bool = True
    use_prioritized_replay: bool = False
    clip_gradients: bool = True
    gradient_clip_value: float = 1.0
    
    # Device
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'