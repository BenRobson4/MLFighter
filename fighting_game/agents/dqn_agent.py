import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
import random
from typing import Dict, List, Any, Tuple
import numpy as np

from .base_agent import MLAgent
from .agent_config import AgentConfig
from ..core import Action


class DQNetwork(nn.Module):
    """Deep Q-Network with configurable architecture"""
    
    def __init__(self, input_size: int, output_size: int, config: AgentConfig):
        super(DQNetwork, self).__init__()
        self.config = config
        
        # Build network layers
        layers = []
        prev_size = input_size
        
        for hidden_size in config.hidden_layers:
            layers.append(nn.Linear(prev_size, hidden_size))
            
            # Activation
            if config.activation == 'relu':
                layers.append(nn.ReLU())
            elif config.activation == 'tanh':
                layers.append(nn.Tanh())
            elif config.activation == 'sigmoid':
                layers.append(nn.Sigmoid())
            
            # Dropout
            if config.dropout_rate > 0:
                layers.append(nn.Dropout(config.dropout_rate))
            
            prev_size = hidden_size
        
        # Output layer
        layers.append(nn.Linear(prev_size, output_size))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class ExperienceReplay:
    """Experience replay buffer with optional prioritization"""
    
    def __init__(self, capacity: int, prioritized: bool = False):
        self.capacity = capacity
        self.prioritized = prioritized
        self.buffer = deque(maxlen=capacity)
        self.priorities = deque(maxlen=capacity) if prioritized else None
    
    def push(self, experience: Tuple, priority: float = 1.0):
        """Add experience to buffer"""
        self.buffer.append(experience)
        if self.prioritized:
            self.priorities.append(priority)
    
    def sample(self, batch_size: int) -> List[Tuple]:
        """Sample batch of experiences"""
        if self.prioritized and self.priorities:
            # Prioritized sampling
            priorities = np.array(self.priorities)
            probs = priorities / priorities.sum()
            indices = np.random.choice(len(self.buffer), batch_size, p=probs)
            return [self.buffer[i] for i in indices]
        else:
            # Uniform sampling
            return random.sample(self.buffer, batch_size)
    
    def __len__(self):
        return len(self.buffer)


class DQNAgent(MLAgent):
    """Deep Q-Learning Agent with configurable features"""
    
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        
        # Feature mapping
        self.feature_indices = self._build_feature_indices()
        self.input_size = len(self.feature_indices)
        self.output_size = len(Action)
        
        # Neural networks
        self.q_network = DQNetwork(self.input_size, self.output_size, self.config).to(self.config.device)
        self.target_network = DQNetwork(self.input_size, self.output_size, self.config).to(self.config.device)
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.config.learning_rate)
        
        # Experience replay
        self.memory = ExperienceReplay(self.config.memory_size, self.config.use_prioritized_replay)
        
        # Training state
        self.epsilon = self.config.epsilon_start
        self.steps = 0
        self.episodes = 0
        self.losses = []
        
    def _build_feature_indices(self) -> Dict[str, int]:
        """Build mapping of feature names to indices in state vector"""
        all_features = [
            'player_x', 'player_y', 'player_health', 'player_velocity_x', 'player_velocity_y',
            'player_is_jumping', 'player_is_blocking', 'player_is_attacking', 'player_attack_cooldown',
            'opponent_x', 'opponent_y', 'opponent_health', 'opponent_velocity_x', 'opponent_velocity_y',
            'opponent_is_jumping', 'opponent_is_blocking', 'opponent_is_attacking', 'opponent_attack_cooldown',
            'distance_x', 'distance_y'
        ]
        
        # Create mapping for included features only
        feature_indices = {}
        idx = 0
        for i, feature in enumerate(all_features):
            if feature in self.config.included_features:
                feature_indices[feature] = idx
                idx += 1
        
        return feature_indices
    
    def _filter_state(self, state: np.ndarray) -> np.ndarray:
        """Filter state vector to include only selected features"""
        all_feature_names = [
            'player_x', 'player_y', 'player_health', 'player_velocity_x', 'player_velocity_y',
            'player_is_jumping', 'player_is_blocking', 'player_is_attacking', 'player_attack_cooldown',
            'opponent_x', 'opponent_y', 'opponent_health', 'opponent_velocity_x', 'opponent_velocity_y',
            'opponent_is_jumping', 'opponent_is_blocking', 'opponent_is_attacking', 'opponent_attack_cooldown',
            'distance_x', 'distance_y'
        ]
        
        filtered = []
        for i, feature in enumerate(all_feature_names):
            if feature in self.config.included_features:
                filtered.append(state[i])
        
        return np.array(filtered, dtype=np.float32)
    
    def get_action(self, state: np.ndarray) -> Action:
        """Select action using epsilon-greedy policy"""
        # Epsilon-greedy exploration
        if random.random() < self.epsilon:
            return Action(random.randint(0, len(Action) - 1))
        
        # Filter state to included features
        filtered_state = self._filter_state(state)
        
        # Get Q-values from network
        with torch.no_grad():
            state_tensor = torch.FloatTensor(filtered_state).unsqueeze(0).to(self.config.device)
            q_values = self.q_network(state_tensor)
            action_idx = q_values.argmax(dim=1).item()
        
        return Action(action_idx)
    
    def update(self, state: np.ndarray, action: Action, reward: float,
               next_state: np.ndarray, done: bool):
        """Update the agent with new experience"""
        # Filter states
        filtered_state = self._filter_state(state)
        filtered_next_state = self._filter_state(next_state)
        
        # Store experience
        self.memory.push((filtered_state, action.value, reward, filtered_next_state, done))
        
        # Update step counter
        self.steps += 1
        
        # Update epsilon
        if done:
            self.episodes += 1
            self.epsilon = max(self.config.epsilon_end, 
                             self.epsilon * self.config.epsilon_decay)
        
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
        # Sample batch from memory
        batch = self.memory.sample(self.config.batch_size)
        
        # Prepare batch tensors
        states = torch.FloatTensor([e[0] for e in batch]).to(self.config.device)
        actions = torch.LongTensor([e[1] for e in batch]).to(self.config.device)
        rewards = torch.FloatTensor([e[2] for e in batch]).to(self.config.device)
        next_states = torch.FloatTensor([e[3] for e in batch]).to(self.config.device)
        dones = torch.FloatTensor([e[4] for e in batch]).to(self.config.device)
        
        # Current Q values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Next Q values
        with torch.no_grad():
            if self.config.use_double_dqn:
                # Double DQN: use online network to select action, target network to evaluate
                next_actions = self.q_network(next_states).argmax(dim=1, keepdim=True)
                next_q_values = self.target_network(next_states).gather(1, next_actions).squeeze(1)
            else:
                # Standard DQN
                next_q_values = self.target_network(next_states).max(dim=1)[0]
            
            # Compute targets
            targets = rewards + (1 - dones) * self.config.gamma * next_q_values
        
        # Compute loss
        loss = F.mse_loss(current_q_values.squeeze(), targets)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping
        if self.config.clip_gradients:
            torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 
                                          self.config.gradient_clip_value)
        
        self.optimizer.step()
        
        # Store loss for monitoring
        self.losses.append(loss.item())
    
    def save(self, filepath: str):
        """Save agent state to file"""
        torch.save({
            'q_network_state': self.q_network.state_dict(),
            'target_network_state': self.target_network.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'config': self.config,  # Save the full config
            'epsilon': self.epsilon,
            'steps': self.steps,
            'episodes': self.episodes,
            'input_size': self.input_size,  # Save network dimensions
            'output_size': self.output_size
        }, filepath)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'DQNAgent':
        """Load agent from file, creating a new agent with saved configuration"""
        checkpoint = torch.load(filepath, map_location='cpu', weights_only=False)
        
        # Create agent with saved configuration
        agent = cls(checkpoint['config'])
        
        # Load network states
        agent.q_network.load_state_dict(checkpoint['q_network_state'])
        agent.target_network.load_state_dict(checkpoint['target_network_state'])
        agent.optimizer.load_state_dict(checkpoint['optimizer_state'])
        
        # Restore training state
        agent.epsilon = checkpoint['epsilon']
        agent.steps = checkpoint['steps']
        agent.episodes = checkpoint['episodes']
        
        return agent

    def load(self, filepath: str):
        """Load agent state from file (keeps current configuration)"""
        checkpoint = torch.load(filepath, map_location=self.config.device, weights_only=False)
        
        # Check if configurations match
        saved_config = checkpoint['config']
        if (saved_config.included_features != self.config.included_features or
            saved_config.hidden_layers != self.config.hidden_layers):
            raise ValueError(
                f"Configuration mismatch! Saved model has different architecture.\n"
                f"Saved features: {saved_config.included_features}\n"
                f"Current features: {self.config.included_features}\n"
                f"Saved layers: {saved_config.hidden_layers}\n"
                f"Current layers: {self.config.hidden_layers}\n"
                f"Use DQNAgent.load_from_file() to load with saved configuration."
            )
        
        self.q_network.load_state_dict(checkpoint['q_network_state'])
        self.target_network.load_state_dict(checkpoint['target_network_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        self.epsilon = checkpoint['epsilon']
        self.steps = checkpoint['steps']
        self.episodes = checkpoint['episodes']   

    def get_stats(self) -> Dict[str, Any]:
        """Get training statistics"""
        return {
            'epsilon': self.epsilon,
            'steps': self.steps,
            'episodes': self.episodes,
            'memory_size': len(self.memory),
            'avg_loss': np.mean(self.losses[-100:]) if self.losses else 0,
            'included_features': list(self.config.included_features)
        }