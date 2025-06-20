import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
import random
from typing import Dict, List, Any, Tuple, Set
import numpy as np

from .base_agent import MLAgent
from .agent_config import AgentConfig
from ..core import Action
from ..ui.option_selector import AgentOption


class AdaptiveConfig:
    """Configuration for adaptive agent with feature masking and reward shaping"""
    
    def __init__(self, fighter: str = 'Default'):
        # Fighter type (can be used for specific configurations)
        self.fighter = fighter

        # All possible features (always same order)
        self.all_features = [
            'player_x', 'player_y', 'player_health', 'player_velocity_x', 'player_velocity_y',
            'player_is_jumping', 'player_is_blocking', 'player_is_attacking', 'player_attack_cooldown',
            'opponent_x', 'opponent_y', 'opponent_health', 'opponent_velocity_x', 'opponent_velocity_y',
            'opponent_is_jumping', 'opponent_is_blocking', 'opponent_is_attacking', 'opponent_attack_cooldown',
            'distance_x', 'distance_y'
        ]
        
        # Active features (can be toggled)
        self.active_features: Set[str] = {
            'player_health', 'opponent_health', 'distance_x'
        }
        
        # Reward weights
        self.reward_weights = {
            'health_gain': 1.0,
            'damage_dealt': 1.0,
            'win_bonus': 100.0,
            'loss_penalty': -100.0,
            'distance_bonus': 0.0,
            'aggression_bonus': 0.0,
            'defense_bonus': 0.0
        }
        
        # Network architecture (fixed for all features)
        self.hidden_layers = [256, 128, 64]  # Large enough for all features
        self.activation = 'relu'
        self.dropout_rate = 0.1
        
        # Learning parameters (adjustable)
        self.learning_rate = 0.001
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
        # Training settings
        self.memory_size = 10000
        self.batch_size = 32
        self.update_frequency = 4
        self.target_update_frequency = 100
        self.use_double_dqn = True
        self.clip_gradients = True
        self.gradient_clip_value = 1.0
        
        # Device
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def get_feature_mask(self) -> np.ndarray:
        """Get binary mask for active features"""
        mask = np.zeros(len(self.all_features), dtype=np.float32)
        for i, feature in enumerate(self.all_features):
            if feature in self.active_features:
                mask[i] = 1.0
        return mask
    
    def update_features(self, new_features: Set[str]):
        """Update active features"""
        self.active_features = new_features & set(self.all_features)
    
    def update_reward_weights(self, weights: Dict[str, float]):
        """Update reward weights"""
        for key, value in weights.items():
            if key in self.reward_weights:
                self.reward_weights[key] = value


class AdaptiveDQNetwork(nn.Module):
    """DQN that handles feature masking"""
    
    def __init__(self, input_size: int, output_size: int, config: AdaptiveConfig):
        super(AdaptiveDQNetwork, self).__init__()
        self.config = config
        
        # Build network for maximum input size
        layers = []
        prev_size = input_size
        
        for hidden_size in config.hidden_layers:
            layers.append(nn.Linear(prev_size, hidden_size))
            
            if config.activation == 'relu':
                layers.append(nn.ReLU())
            elif config.activation == 'tanh':
                layers.append(nn.Tanh())
            
            if config.dropout_rate > 0:
                layers.append(nn.Dropout(config.dropout_rate))
            
            prev_size = hidden_size
        
        layers.append(nn.Linear(prev_size, output_size))
        self.network = nn.Sequential(*layers)
    
    def forward(self, x, feature_mask=None):
        """Forward pass with optional feature masking"""
        if feature_mask is not None:
            x = x * feature_mask
        return self.network(x)


class AdaptiveDQNAgent(MLAgent):
    """DQN Agent with adaptive feature selection and reward shaping"""
    
    def __init__(self, config: AdaptiveConfig = None, player_id: str = "player1"):
        self.config = config or AdaptiveConfig()
        self.player_id = player_id
        
        # Network setup (always uses all features)
        self.input_size = len(self.config.all_features)
        self.output_size = len(Action)
        
        # Neural networks
        self.q_network = AdaptiveDQNetwork(
            self.input_size, self.output_size, self.config
        ).to(self.config.device)
        
        self.target_network = AdaptiveDQNetwork(
            self.input_size, self.output_size, self.config
        ).to(self.config.device)
        
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.q_network.parameters(), 
            lr=self.config.learning_rate
        )
        
        # Experience replay
        self.memory = deque(maxlen=self.config.memory_size)
        
        # Training state
        self.epsilon = self.config.epsilon
        self.steps = 0
        self.episodes = 0
        self.losses = []
        
        # Feature mask
        self.feature_mask = None
        self.update_feature_mask()
    
    def update_feature_mask(self):
        """Update the feature mask based on active features"""
        self.feature_mask = torch.FloatTensor(
            self.config.get_feature_mask()
        ).to(self.config.device)
    
    def update_configuration(self, fighter: str = None,
                           features: Set[str] = None, 
                           reward_weights: Dict[str, float] = None,
                           epsilon: float = None,
                           epsilon_decay: float = None,
                           learning_rate: float = None):
        """Update agent configuration during training"""
        if fighter is not None:
            self.config.fighter = fighter
        
        if features is not None:
            self.config.update_features(features)
            self.update_feature_mask()
        
        if reward_weights is not None:
            self.config.update_reward_weights(reward_weights)
        
        if epsilon is not None:
            self.epsilon = epsilon
            self.config.epsilon = epsilon
        
        if epsilon_decay is not None:
            self.config.epsilon_decay = epsilon_decay
        
        if learning_rate is not None:
            self.config.learning_rate = learning_rate
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = learning_rate
    
    def get_action(self, state: np.ndarray) -> Action:
        """Select action using epsilon-greedy policy"""
        if random.random() < self.epsilon:
            return Action(random.randint(0, len(Action) - 1))
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.config.device)
            q_values = self.q_network(state_tensor, self.feature_mask)
            action_idx = q_values.argmax(dim=1).item()
        
        return Action(action_idx)
    
    def calculate_shaped_reward(self, state: np.ndarray, action: Action, 
                               next_state: np.ndarray, base_reward: float, 
                               done: bool, info: Dict[str, Any] = None) -> float:
        """Calculate shaped reward based on configuration"""
        shaped_reward = 0.0
        w = self.config.reward_weights
        
        # Base health rewards
        if info:
            health_gain = info.get('health_change', 0)
            damage_dealt = info.get('damage_dealt', 0)
            
            shaped_reward += w['health_gain'] * health_gain
            shaped_reward += w['damage_dealt'] * damage_dealt
            
            # Distance-based rewards
            if w['distance_bonus'] != 0:
                distance = state[18] if len(state) > 18 else 0  # distance_x feature
                shaped_reward += w['distance_bonus'] * (1 - distance)
            
            # Action-based rewards
            if action == Action.ATTACK:
                shaped_reward += w['aggression_bonus']
            elif action == Action.BLOCK:
                shaped_reward += w['defense_bonus']
        
        # Win/loss rewards
        if done:
            if base_reward > 0:  # Won
                shaped_reward += w['win_bonus']
            else:  # Lost
                shaped_reward += w['loss_penalty']
        
        return shaped_reward + base_reward * 0.1  # Include some base reward
    
    def update(self, state: np.ndarray, action: Action, reward: float,
               next_state: np.ndarray, done: bool, info: Dict[str, Any] = None):
        """Update the agent with new experience"""
        # Calculate shaped reward
        shaped_reward = self.calculate_shaped_reward(
            state, action, next_state, reward, done, info
        )
        
        # Store experience
        self.memory.append((state, action.value, shaped_reward, next_state, done))
        
        # Update step counter
        self.steps += 1
        
        # Update epsilon
        if done:
            self.episodes += 1
            self.epsilon = max(
                self.config.epsilon_min,
                self.epsilon * self.config.epsilon_decay
            )
        
        # Skip training if not enough samples
        if len(self.memory) < self.config.batch_size:
            return
        
        # Train at specified frequency
        if self.steps % self.config.update_frequency == 0:
            self._train_step()
        
        # Update target network
        if self.steps % self.config.target_update_frequency == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
    
    def _train_step(self):
        """Perform one training step"""
        # Sample batch
        batch = random.sample(self.memory, self.config.batch_size)
        
        # Prepare tensors
        states = torch.FloatTensor([e[0] for e in batch]).to(self.config.device)
        actions = torch.LongTensor([e[1] for e in batch]).to(self.config.device)
        rewards = torch.FloatTensor([e[2] for e in batch]).to(self.config.device)
        next_states = torch.FloatTensor([e[3] for e in batch]).to(self.config.device)
        dones = torch.FloatTensor([e[4] for e in batch]).to(self.config.device)
        
        # Apply feature mask
        states = states * self.feature_mask
        next_states = next_states * self.feature_mask
        
        # Current Q values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values
        with torch.no_grad():
            if self.config.use_double_dqn:
                next_actions = self.q_network(next_states).argmax(dim=1, keepdim=True)
                next_q_values = self.target_network(next_states).gather(1, next_actions).squeeze(1)
            else:
                next_q_values = self.target_network(next_states).max(dim=1)[0]
            
            targets = rewards + (1 - dones) * self.config.gamma * next_q_values
        
        # Loss and optimization
        loss = F.mse_loss(current_q_values.squeeze(), targets)
        
        self.optimizer.zero_grad()
        loss.backward()
        
        if self.config.clip_gradients:
            torch.nn.utils.clip_grad_norm_(
                self.q_network.parameters(), 
                self.config.gradient_clip_value
            )
        
        self.optimizer.step()
        self.losses.append(loss.item())
    
    def save(self, filepath: str):
        """Save agent state including current epsilon and all parameters"""
        torch.save({
            'q_network_state': self.q_network.state_dict(),
            'target_network_state': self.target_network.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'config': self.config,
            'epsilon': self.epsilon,  # Current epsilon after decay
            'steps': self.steps,
            'episodes': self.episodes,
            'memory': list(self.memory),  # Save experience replay
            'losses': self.losses[-1000:] if len(self.losses) > 1000 else self.losses  # Save recent losses
        }, filepath)

    @classmethod
    def load_from_file(cls, filepath: str, player_id: str = "player1") -> 'AdaptiveDQNAgent':
        """Load agent from file, restoring exact state"""
        checkpoint = torch.load(filepath, map_location='cpu')
        
        # Create agent with saved configuration
        agent = cls(checkpoint['config'], player_id)
        
        # Load network states
        agent.q_network.load_state_dict(checkpoint['q_network_state'])
        agent.target_network.load_state_dict(checkpoint['target_network_state'])
        agent.optimizer.load_state_dict(checkpoint['optimizer_state'])
        
        # Restore training state
        agent.epsilon = checkpoint['epsilon']  # Use saved epsilon, not config
        agent.steps = checkpoint['steps']
        agent.episodes = checkpoint['episodes']
        
        # Restore memory if available
        if 'memory' in checkpoint and checkpoint['memory']:
            agent.memory = deque(checkpoint['memory'], maxlen=agent.config.memory_size)
        
        # Restore losses if available
        if 'losses' in checkpoint:
            agent.losses = checkpoint['losses']
        
        return agent

    def get_current_config(self) -> AgentOption:
        """Get current configuration as AgentOption"""
        from ..ui.option_selector import AgentOption
        return AgentOption(
            fighter=self.config.fighter,
            features=set(self.config.active_features),
            epsilon=self.epsilon,  # Use current epsilon, not config
            decay=self.config.epsilon_decay,
            learning_rate=self.config.learning_rate
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get training statistics"""
        return {
            'epsilon': self.epsilon,
            'steps': self.steps,
            'episodes': self.episodes,
            'memory_size': len(self.memory),
            'avg_loss': np.mean(self.losses[-100:]) if self.losses else 0,
            'active_features': list(self.config.active_features),
            'learning_rate': self.config.learning_rate
        }